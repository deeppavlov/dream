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
            attr = {}
            # TODO check correct order of concatenation of replies
            try:
                annotations = dialog["utterances"][-1]["annotations"]
                intents = annotations["cobot_dialogact"]["intents"]
                opinion_request_detected = annotations["intent_catcher"].get(
                    "opinion_request", {}).get("detected") == 1
                logger.info(f"intents {intents}")
                if ("Opinion_RequestIntent" in intents) or opinion_request_detected:
                    logger.info(f"intents {intents}")
                    # TODO: check whether the opinion is already in attributes
                    reply, subject_attitude = self.templates.give_opinion(dialog)
                    current_reply += reply
                    for subject in subject_attitude:
                        attr[subject] = subject_attitude[subject]
                    confidence = self.default_conf
                if "Information_RequestIntent" in intents:
                    # TODO: we can answer actually for some of the questions
                    # TODO: for difficult questions we have cobotqa
                    reply = self.templates.give_factual_answer(dialog)
                    current_reply += reply
                    confidence = self.default_conf
                if "Opinion_DeliveryIntent" in intents:
                    # TODO: attitude is not sentiment actually
                    attitude = dialog["utterances"][-1]["annotations"]["cobot_sentiment"]["text"]
                    # TODO:  what if subject `this actor`?
                    # TODO: extract subject using templates
                    subject = dialog["utterances"][-1]["annotations"]["nounphrases"]["text"]
                    human_attr[subject] = attitude
                    confidence = self.default_conf
                    current_reply += reply
                if "Information_DeliveryIntent" in intents:
                    # заглушка с ответом "о круто я не знала"
                    # TODO: ask a question about opinion or fact
                    reply = self.templates.didnotknowbefore()
                    confidence = self.default_conf
                    current_reply += reply
            except Exception as e:
                logger.exception(f"exception in movie skill {e}")
                with sentry_sdk.push_scope() as scope:
                    dialog_replies = []
                    for reply in dialog["utterances"]:
                        dialog_replies.append(reply["text"])
                    # This will be changed only for the error caught inside and automatically discarded afterward
                    scope.set_extra('dialogs', dialog_replies)
                    sentry_sdk.capture_exception(e)

            texts.append(current_reply)
            confidences.append(confidence)
            human_attributes.append(human_attr)
            bot_attributes.append(bot_attr)
            attributes.append(attr)

        return texts, confidences, human_attributes, bot_attributes, attributes
