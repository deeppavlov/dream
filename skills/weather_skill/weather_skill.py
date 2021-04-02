import logging
from os import getenv
import re
import sentry_sdk
import pprint
from collections import defaultdict
from city_slot import OWMCitySlot
from common.constants import CAN_CONTINUE_SCENARIO, MUST_CONTINUE
from common.link import link_to, SKILLS_TO_BE_LINKED_EXCEPT_LOW_RATED
from common.weather import is_weather_for_homeland_requested, is_weather_without_city_requested


sentry_sdk.init(getenv('SENTRY_DSN'))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

city_slot_obj = OWMCitySlot()
blacklist_cities = {'is', 'none', 'ok', 'okay'}


class DialogDataManager():
    def __init__(self, dialog_data):
        self.d = dialog_data

    def get_last_utterance_dict(self):
        return self.d["utterances"][-1]

    def get_last_bot_utterance_dict(self):
        if len(self.d["utterances"]) >= 2:
            return self.d["utterances"][-2]
        else:
            return None

    def load_attrs_from_dialog(self):
        """
        Manager method to load attrs from previous utterance because context transfer in dp_agent
        sucks...
        :return: attrs dict
        """
        if len(self.d['human_utterances']) > 1:
            hypotheses_dicts_list = self.d["human_utterances"][-2]["hypotheses"]
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

    def get_preferred_weather(self, weather_dict, utterance_dict=None):
        """
        retrieves weather from user answer
        :param weather_dict: dictionary of weather alliasies
        :return: weather string or None, if not found
        """
        if not utterance_dict:
            # look for answer in the last utterance
            utterance_dict = self.get_last_utterance_dict()

        detected_weather = None
        for weather in weather_dict:
            re_weather = r".*" + r"|".join(['(' + s + ')' for s in weather_dict[weather]['synonyms']]) + r"( |,|\.|$)"
            if re.match(re_weather, utterance_dict['text'].lower()):
                detected_weather = weather
        return detected_weather

    def retrieve_location_entity_from_utterance(self, utterance_dict=None):
        """
        retrieves the first extracted entity from utterance dict
        :param utterance_dict: raw dictionary with serialization of Utterance object.
        :return: city string
        """
        if not utterance_dict:
            # by default provide location extraction from last reply
            utterance_dict = self.get_last_utterance_dict()

        # ### Alternative GEO extractor:
        city = city_slot_obj(utterance_dict['text'])
        if not city:
            # if not extracted lets try to grab from NER?
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
        logger.info(f"Extracted city `{city}` from user utterance.")
        city = city or ''
        if city.lower().strip() not in blacklist_cities:
            return city
        else:
            return None


# default confidence
BASE_CONFIDENCE = 0.0

# confidence when we ready to provide forecast
FORECAST_CONFIDENCE = 1.

# confidence when we asking auxillary questions for providing weather forecast
QUESTION_CONFIDENCE = 0.999

# confindce when asking smalltalk questions, e.g. "Let me guess - you like skiing?"
SMALLTALK_CONFIDENCE = 0.999

# when we asked the city, but can not recognize city by NER nor by
MISSED_CITY_CONFIDENCE = 0.98


class WeatherSkill:
    def __init__(self, weather_dict={}):
        self.weather_dict = weather_dict

    def process_dialog(self, dialog):
        """Method of a dialog analysis"""

        question_phrase = "What weather do you prefer? Warm, cold, rain, snow, hot?"
        city_slot_requested = 'weather_forecast_interaction_city_slot_requested'

        # 1. check intent of weather request in annotations
        # 2. retrieve a city slot from usermessage (use NER? or Personal Info skill)
        curr_confidence = BASE_CONFIDENCE
        current_reply = ""
        bot_attr = {}
        human_attr = dialog["human"]["attributes"]
        human_attr["used_links"] = human_attr.get("used_links", defaultdict(list))
        weather_for_homeland_requested = False
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
            weather_without_city_requested = False
            if len(dialog["utterances"]) > 1:
                prev_bot_utt = dialog["utterances"][-2]
                user_utt = dialog["utterances"][-1]
                weather_for_homeland_requested = is_weather_for_homeland_requested(prev_bot_utt, user_utt)
                weather_without_city_requested = is_weather_without_city_requested(prev_bot_utt, user_utt)
            if annotations.get("intent_catcher", {}).get("weather_forecast_intent", {}).get(
                    "detected", 0) == 1 or weather_without_city_requested:
                logger.warning("WEATHER FORECAST INTENT DETECTED")
                ############################################################
                # retrieve city slot or enqueue question into agenda
                ############################################################
                city_str = d_man.retrieve_location_entity_from_utterance()
                if city_str:
                    ############################################################
                    # provide FORECAST
                    ############################################################

                    context_dict['weather_forecast_interaction_city_slot_raw'] = city_str
                    context_dict[city_slot_requested] = False
                    context_dict['can_continue'] = MUST_CONTINUE
                    context_dict['weather_forecast_interaction_question_asked'] = True

                    weather_forecast_str = self.request_weather_service(city_str)
                    current_reply = weather_forecast_str + ". " + question_phrase
                    curr_confidence = FORECAST_CONFIDENCE
                else:
                    ############################################################
                    # request CITY SLOT
                    ############################################################
                    # ask question:
                    current_reply = "Hmm. Which particular city would you like a weather forecast for?"
                    context_dict[city_slot_requested] = True
                    if weather_without_city_requested:
                        curr_confidence = FORECAST_CONFIDENCE
                    else:
                        curr_confidence = QUESTION_CONFIDENCE
                return current_reply, curr_confidence, human_attr, bot_attr, context_dict
            elif context_dict.get(city_slot_requested, False) or weather_for_homeland_requested:
                logger.warning("WEATHER FORECAST city_slot_requested already! Handling!")
                ############################################################
                # check if we handling response for the question about city slot
                ############################################################
                city = d_man.retrieve_location_entity_from_utterance()
                context_dict[city_slot_requested] = False

                if weather_for_homeland_requested:
                    city = dialog["human"]["profile"].get('location')

                if city:
                    # TODO announce fulfilled intent
                    ############################################################
                    # provide FORECAST
                    ############################################################
                    context_dict['weather_forecast_interaction_city_slot_raw'] = city
                    context_dict['can_continue'] = CAN_CONTINUE_SCENARIO
                    context_dict['weather_forecast_interaction_question_asked'] = True
                    weather_forecast_str = self.request_weather_service(city)
                    current_reply = weather_forecast_str + ". " + question_phrase
                    curr_confidence = FORECAST_CONFIDENCE
                else:
                    # we have been ignored?
                    # we have not extracted city?
                    # ignore and forget everything
                    ############################################################
                    # FORGET because it is a complex case. tell a joke about weather?
                    ############################################################
                    current_reply = "Sorry, I have no weather for the place. I didn't recognize the city..."
                    context_dict['can_continue'] = CAN_CONTINUE_SCENARIO
                    curr_confidence = MISSED_CITY_CONFIDENCE
            elif context_dict.get("weather_forecast_interaction_question_asked", False):
                logger.warning("WEATHER INTERACTION QUESTION ASKED")
                weather = d_man.get_preferred_weather(self.weather_dict)
                context_dict['weather_forecast_interaction_question_asked'] = False
                if weather:
                    # recognized preferred weather type, return one of the templated answers
                    ############################################################
                    # provide templated answer
                    ############################################################
                    curr_confidence = SMALLTALK_CONFIDENCE
                    context_dict['weather_forecast_interaction_preferred_weather'] = weather
                    context_dict['can_continue'] = MUST_CONTINUE
                    current_reply = self.weather_dict[weather]['question']
                else:
                    # we have been ignored?
                    # we haven't recognized the weather?
                    # just ignore us
                    ############################################################
                    # INGORE
                    ############################################################
                    context_dict['weather_forecast_interaction_preferred_weather'] = False
                    context_dict['can_continue'] = CAN_CONTINUE_SCENARIO
            elif context_dict.get("weather_forecast_interaction_preferred_weather", False):
                logger.warning("WEATHER PREFFERED WEATHER GOT")
                # got preferred weather from user and asked him a "let me guess" question
                ############################################################
                # provide templated answer
                ############################################################
                context_dict['can_continue'] = CAN_CONTINUE_SCENARIO
                user_utterance = d_man.get_last_utterance_dict()['text']
                if not re.match(".*(i|I) (don't|do not) like.*", user_utterance):
                    # talk more about hiking/swimming/skiing/etc.
                    curr_confidence = SMALLTALK_CONFIDENCE
                    weather = context_dict["weather_forecast_interaction_preferred_weather"]
                    context_dict['weather_forecast_interaction_preferred_weather'] = False
                    link = link_to(SKILLS_TO_BE_LINKED_EXCEPT_LOW_RATED, used_links=human_attr["used_links"],
                                   recent_active_skills=["weather_skill"])
                    human_attr["used_links"][link["skill"]] = human_attr["used_links"].get(
                        link["skill"], []) + [link['phrase']]
                    current_reply = self.weather_dict[weather]['answer'] + " " + link["phrase"]
                else:
                    # don't talk about hiking/swimming/skiing/etc.
                    pass
            else:
                pass
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
