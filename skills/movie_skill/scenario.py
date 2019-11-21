import logging

from templates import MovieSkillTemplates

from os import getenv
import sentry_sdk

sentry_sdk.init(getenv('SENTRY_DSN'))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


class MovieSkillScenario:

    def __init__(self):
        self.default_conf = 0.98
        self.templates = MovieSkillTemplates()

    def __call__(self, dialogs):
        texts = []
        confidences = []
        human_attributes = []
        bot_attributes = []
        attributes = []

        for dialog in dialogs:
            confidence = 0.1
            current_reply = ""
            human_attr = {}
            bot_attr = {}
            attr = {"bot_attitudes": [], "human_attitudes": []}
            # TODO check correct order of concatenation of replies
            try:
                annotations = dialog["utterances"][-1]["annotations"]
                intents = annotations["cobot_dialogact"]["intents"]
                opinion_request_detected = annotations["intent_catcher"].get(
                    "opinion_request", {}).get("detected") == 1
                logger.info(f"intents {intents}")
                if "Opinion_ExpressionIntent" in intents or "Information_DeliveryIntent" in intents:
                    attitude = dialog["utterances"][-1]["annotations"]["attitude_classification"]["text"]
                    reply, subject_attitude = self.templates.get_user_opinion(dialog, attitude)
                    for subject in subject_attitude:
                        attr["human_attitudes"] += [subject]
                    confidence = self.default_conf
                    current_reply += " " + reply
                if (("Information_RequestIntent"
                     in intents) or ("Opinion_RequestIntent" in intents) or opinion_request_detected):
                    reply, subject_attitude = self.templates.give_opinion(dialog)
                    current_reply += " " + reply
                    for subject in subject_attitude:
                        attr["bot_attitudes"] += [subject]
                    confidence = self.default_conf
                if "Information_DeliveryIntent" in intents:
                    pass
                    # TODO: ask a question about opinion or fact
                    # reply = self.templates.didnotknowbefore()
                    # confidence = self.default_conf
                    # current_reply += " " + reply
            except Exception as e:
                logger.exception(f"exception in movie skill {e}")
                with sentry_sdk.push_scope() as scope:
                    dialog_replies = []
                    for reply in dialog["utterances"]:
                        dialog_replies.append(reply["text"])
                    # This will be changed only for the error caught inside and automatically discarded afterward
                    scope.set_extra('dialogs', dialog_replies)
                    sentry_sdk.capture_exception(e)

            texts.append(current_reply.strip())
            confidences.append(confidence)
            human_attributes.append(human_attr)
            bot_attributes.append(bot_attr)
            attributes.append(attr)

        return texts, confidences, human_attributes, bot_attributes, attributes
