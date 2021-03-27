import logging
import sentry_sdk
from collections import defaultdict
from os import getenv

from common.grounding import what_we_talk_about
from common.utils import get_topics, get_intents
from utils import get_intent_dict, get_da_topic_dict, get_cobot_topic_dict, \
    MIDAS_INTENT_ACKNOWLEDGMENETS, get_midas_intent_acknowledgement, reformulate_question_to_statement

sentry_sdk.init(getenv('SENTRY_DSN'))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_CONF = 0.99
DONTKNOW_CONF = 0.5
DONTKNOW_PHRASE = "Seems like I have no idea what we are talking about."


class GroundingSkillScenario:

    def __init__(self):
        pass

    def __call__(self, dialogs):
        texts = []
        confidences = []
        human_attributes, bot_attributes, attributes = [], [], []
        for dialog in dialogs:
            curr_responses, curr_confidences, curr_human_attrs, curr_bot_attrs, curr_attrs = [], [], [], [], []

            bot_attr = {}
            human_attr = dialog["human"]["attributes"]
            human_attr["used_links"] = human_attr.get("used_links", defaultdict(list))
            attr = {}
            what_do_you_mean_intent = dialog["human_utterances"][-1].get(
                "annotations", {}).get(
                "intent_catcher", {}).get(
                "what_are_you_talking_about", {}).get(
                "detected", False)
            try:
                if not (what_we_talk_about(dialog['human_utterances'][-1]) or what_do_you_mean_intent):
                    reply, confidence = '', 0
                elif len(dialog.get('human_utterances', [])) < 2:
                    reply, confidence = DONTKNOW_PHRASE, DONTKNOW_CONF
                else:
                    prev_annotations = dialog['human_utterances'][-2].get('annotations', dict())
                    logger.debug('Running grounding skill')

                    entity_list = []
                    for tmp in prev_annotations.get('ner', []):
                        if len(tmp) > 0 and 'text' in tmp[0]:
                            entity_list.append(tmp[0]['text'])
                    if len(entity_list) == 1:
                        entity_name = entity_list[0]
                    elif len(entity_list) > 1:
                        entity_name = ','.join(entity_list[::-1]) + ' and ' + entity_list[-1]
                    else:
                        entity_name = ''
                    intent_dict = get_intent_dict(entity_name)
                    intents_by_popularity = list(intent_dict.keys())[::-1]
                    intent_list = get_intents(dialog['human_utterances'][-2], which='cobot_dialogact_intents')
                    if 'text' in intent_list:
                        intent_list = intent_list['text']
                    intent_list = list(set(intent_list))
                    logger.info(f'Intents received {intent_list}')
                    da_topic_list = get_topics(dialog['human_utterances'][-2], which='cobot_dialogact_topics')
                    if 'text' in da_topic_list:
                        da_topic_list = da_topic_list['text']
                    da_topic_list = list(set(da_topic_list))
                    da_topic_dict = get_da_topic_dict()
                    da_topics_by_popularity = list(da_topic_dict.keys())[::-1]

                    cobot_topic_list = get_topics(dialog['human_utterances'][-2], which='cobot_topics')
                    if 'text' in cobot_topic_list:
                        cobot_topic_list = cobot_topic_list['text']
                    cobot_topic_list = list(set(cobot_topic_list))
                    cobot_topic_dict = get_cobot_topic_dict()
                    cobot_topics_by_popularity = list(cobot_topic_dict.keys())[::-1]
                    reply = None
                    for intent in intents_by_popularity:  # start from least popular
                        if intent in intent_list and reply is None and len(entity_name) > 0:
                            reply = intent_dict[intent]
                    if len(entity_name) > 0 and reply is None:
                        reply = f"We are discussing {entity_name}, aren't we?"
                    for topic in da_topics_by_popularity:  # start from least popular
                        if topic in da_topic_list and reply is None:
                            reply = da_topic_dict[topic]
                    for topic in cobot_topics_by_popularity:  # start from least popular
                        if topic in cobot_topic_list and reply is None:
                            reply = cobot_topic_dict[topic]
                    if reply is None:
                        reply, confidence = DONTKNOW_PHRASE, DONTKNOW_CONF
                    else:
                        confidence = DEFAULT_CONF
                    logger.info(f'Grounding skill output: {reply} {confidence}')
            except Exception as e:
                logger.exception("exception in grounding skill")
                logger.info(str(e))
                sentry_sdk.capture_exception(e)
                reply = ""
                confidence = 0

            curr_responses += [reply]
            curr_confidences += [confidence]
            curr_human_attrs += [human_attr]
            curr_bot_attrs += [bot_attr]
            curr_attrs += [attr]

            # ACKNOWLEDGEMENT HYPOTHESES for current utterance
            curr_intents = get_intents(dialog['human_utterances'][-1], probs=False, which='midas')
            curr_considered_intents = [intent for intent in curr_intents if intent in MIDAS_INTENT_ACKNOWLEDGMENETS]

            if curr_considered_intents:
                # can generate acknowledgement
                is_need_nounphrase_intent = any([intent in curr_intents for intent in ["open_question_opinion"]])
                if is_need_nounphrase_intent:
                    curr_nounphrase = dialog['human_utterances'][-1]["annotations"].get("cobot_nounphrases", [])
                    curr_nounphrase = curr_nounphrase[-1] if len(curr_nounphrase) > 0 and curr_nounphrase[-1] else ""
                    ackn_response = get_midas_intent_acknowledgement(curr_considered_intents[-1], curr_nounphrase)
                else:
                    curr_reformulated_question = reformulate_question_to_statement(
                        dialog['human_utterances'][-1]["text"])
                    ackn_response = get_midas_intent_acknowledgement(curr_considered_intents[-1],
                                                                     curr_reformulated_question)
                curr_responses += [ackn_response]
                curr_confidences += [0.5]
                curr_human_attrs += [{}]
                curr_bot_attrs += [{}]
                curr_attrs += [{"response_parts": ["acknowledgement"]}]

            texts.append(curr_responses)
            confidences.append(curr_confidences)
            human_attributes.append(curr_human_attrs)
            bot_attributes.append(curr_bot_attrs)
            attributes.append(curr_attrs)

        return texts, confidences, human_attributes, bot_attributes, attributes
