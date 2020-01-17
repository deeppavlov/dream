import logging
from os import getenv
import sentry_sdk
import pprint
sentry_sdk.init(getenv('SENTRY_DSN'))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


class DialogDataManager():
    def __init__(self, dialog_data):
        self.d = dialog_data

    def get_last_utterance_dict(self):
        return self.d["utterances"][-1]

    def load_attrs_from_dialog(self):
        """
        Manager method to load attrs from previous utterance because context transfer in dp_agent
        sucks...
        :return: attrs dict
        """
        if len(self.d['utterances']) > 2:
            hypotheses_dicts_list = self.d["utterances"][-3]["hypotheses"]
            hypo_dict = self.find_hypothesis_of_skill(hypotheses_dicts_list)
            if hypo_dict:
                attr = hypo_dict
                # prune system fileds: text & confidence
                del attr['text']
                del attr['confidence']

            else:
                attr = {}
        else:
            attr = {}

        return attr

    def find_hypothesis_of_skill(self, hypotheses_dicts_list, skill_name="weather_skill"):
        for each_hypo_dict in hypotheses_dicts_list:
            if each_hypo_dict['skill_name'] == skill_name:
                return each_hypo_dict
        else:
            return None

    def retrieve_location_entity_from_utterance(self, utterance_dict=None):
        """
        retrieves the first extracted entity froim utterance dict
        :param utterance:
        :return: city string
        """
        if not utterance_dict:
            # by default provide location extraction from last reply
            utterance_dict = self.get_last_utterance_dict()

        annotations = utterance_dict["annotations"]
        city = None
        # logger.info("entities in lastest annotation:")
        # logger.info(annotations["ner"])
        for ent in annotations["ner"]:
            if not ent:
                continue
            ent = ent[0]
            if ent['type'] == "LOC":
                city = ent['text']
                # TODO normalize city...?
                # TODO validate city?

        # TODO No NER detected location case?
        # TODO detect from keywords search
        return city


# default confidence
BASE_CONFIDENCE = 0.0

# confidence when we ready to provide forecast
FORECAST_CONFIDENCE = 0.999

# confidence when we asking auxillary questions for providing weather forecast:
QUESTION_CONFIDENCE = 0.999


class WeatherSkill:
    def process_dialog(self, dialog):
        """Method of a dialog analysis"""

        # 1. check intent of weather request in annotations
        # 2. retrieve a city slot from usermessage (use NER? or Personal Info skill)
        curr_confidence = BASE_CONFIDENCE
        current_reply = ""
        human_attr = {}
        bot_attr = {}
        # TODO load attrs?
        ######################################################################
        #
        d_man = DialogDataManager(dialog)
        context_dict = d_man.load_attrs_from_dialog()
        logger.warning("======================================")
        logger.warning(pprint.pformat(context_dict))

        ######################################################################
        # TODO check correct order of concatenation of replies
        try:
            ############################################################
            # check if weather intent triggered in last utterance:
            ############################################################
            annotations = dialog["utterances"][-1]["annotations"]
            if annotations.get("intent_catcher", {}).get("weather_forecast_intent", {}).get(
                    "detected", 0) == 1:
                logger.warning("WEATHER FORECAST INTENT DETECTED")
                ############################################################
                # retrieve city slot or enqueue question into agenda
                ############################################################
                city_str = d_man.retrieve_location_entity_from_utterance()
                if city_str:
                    ############################################################
                    # provde FORECAST
                    ############################################################
                    context_dict['weather_forecast_interaction_city_slot_raw'] = city_str
                    weather_forecast_str = self.request_weather_service(city_str)
                    current_reply = weather_forecast_str
                    curr_confidence = FORECAST_CONFIDENCE
                    return current_reply, curr_confidence, human_attr, bot_attr, context_dict
                else:
                    ############################################################
                    # request CITY SLOT
                    ############################################################
                    # ask question:
                    current_reply = "For which city do you want to get weather forecast?"
                    context_dict['weather_forecast_interaction_city_slot_requested'] = True
                    curr_confidence = QUESTION_CONFIDENCE
                    return current_reply, curr_confidence, human_attr, bot_attr, context_dict

            elif context_dict.get("weather_forecast_interaction_city_slot_requested", False):
                logger.warning("WEATHER FORECAST city_slot_requested already! Handling!")
                ############################################################
                # check if we handling response for the question about city slot
                ############################################################
                city = d_man.retrieve_location_entity_from_utterance()
                context_dict['weather_forecast_interaction_city_slot_requested'] = False

                if city:
                    # TODO announce fulfilled intent
                    ############################################################
                    # provde FORECAST
                    ############################################################
                    context_dict['weather_forecast_interaction_city_slot_raw'] = city
                    weather_forecast_str = self.request_weather_service(city)
                    current_reply = weather_forecast_str
                    curr_confidence = FORECAST_CONFIDENCE
                    return current_reply, curr_confidence, human_attr, bot_attr, context_dict

                else:
                    # we have been ignored?
                    # we have not extracted city?
                    # ignore and forget everything
                    ############################################################
                    # FORGET because it is a complex case. tell a joke about weather?
                    ############################################################
                    current_reply = "Sorry, I have no weather for the place. I can not understand the city..."
                    curr_confidence = 0.5
                    return current_reply, curr_confidence, human_attr, bot_attr, context_dict
            else:
                # just ignore
                return current_reply, curr_confidence, human_attr, bot_attr, context_dict

        except Exception as e:
            logger.exception(f"exception in weather skill {e}")
            with sentry_sdk.push_scope() as scope:
                dialog_replies = []
                for reply in dialog["utterances"]:
                    dialog_replies.append(reply["text"])
                # This will be changed only for the error caught inside and automatically discarded afterward
                scope.set_extra('dialogs', dialog_replies)
                sentry_sdk.capture_exception(e)

        return current_reply, curr_confidence, human_attr, bot_attr, context_dict

    def request_weather_service(self, location_str, timeperiod=None):
        """bridge method to service"""
        print("requesting weather for %s at %s" % (location_str, timeperiod))
        from weather_service import weather_forecast_now
        # from .weather_service import weather_forecast_now
        return weather_forecast_now(location_str)

    def __call__(self, dialogs):
        """Main method for batchy handling"""
        texts = []
        confidences = []
        human_attributes = []
        bot_attributes = []
        attributes = []

        for dialog in dialogs:
            current_reply, curr_confidence, human_attr, bot_attr, attr = self.process_dialog(dialog)
            texts.append(current_reply.strip())

            confidences.append(curr_confidence)
            human_attributes.append(human_attr)
            bot_attributes.append(bot_attr)
            attributes.append(attr)
        logger.warning("============WEATHER SKILL ANSWERS:==========================")
        logger.warning(texts)
        logger.warning("============ANSWERS==========================")
        return texts, confidences, human_attributes, bot_attributes, attributes
