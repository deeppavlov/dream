import logging
import sentry_sdk
from collections import defaultdict
from os import getenv

from common.grounding import what_we_talk_about
from common.utils import get_topics, get_intents

sentry_sdk.init(getenv('SENTRY_DSN'))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_CONF = 0.99
DONTKNOW_CONF = 0.5
DONTKNOW_PHRASE = "I don't know what are we talking about"


class GroundingSkillScenario:

    def __init__(self):
        pass

    def __call__(self, dialogs):
        texts = []
        confidences = []
        human_attributes, bot_attributes, attributes = [], [], []
        for dialog in dialogs:
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
                    reply = 'To my understanding, we are talking'

                    entity_list = []
                    for tmp in prev_annotations.get('ner', []):
                        if len(tmp) > 0 and 'text' in tmp[0]:
                            entity_list.append(tmp[0]['text'])
                    my_entities = ', '.join([str(k) for k in sorted(entity_list)])

                    topic_list1 = get_topics(dialog['human_utterances'][-2], which='cobot_topics')
                    topic_list2 = get_topics(dialog['human_utterances'][-2], which='cobot_dialogact_topics')

                    topic_list = topic_list1 + topic_list2

                    topic_list = list(set(topic_list))
                    topic_list = [j.replace('_', ' ') for j in topic_list if j not in ['Other', 'Phatic']]
                    my_topics = ', '.join([str(k) for k in sorted(topic_list)])

                    intent_list = get_intents(dialog['human_utterances'][-2], which='cobot_dialogact_intents')
                    if 'text' in intent_list:
                        intent_list = intent_list['text']

                    intent_list = [j.replace('_', ' ').replace('Intent', ' Intent') for j in intent_list if
                                   j != 'OtherIntent']
                    my_intents = ', '.join([str(k) for k in sorted(intent_list)])

                    logger.debug('Found entities topics intents')
                    logger.debug(f' {entity_list} {topic_list} {intent_list}')

                    if len(topic_list) > 0:
                        reply = f'{reply} about the following topics: {my_topics}'
                    if len(intent_list) > 0:
                        reply = f'{reply} with the following intents: {my_intents}.'
                    if len(entity_list) > 0:
                        if len(topic_list) == len(intent_list) == 0:
                            reply += 'I see '
                        else:
                            reply += 'I also see '
                        reply = f'{reply} that you have mentioned the following entities: {my_entities}.'
                    if reply == '':
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
            texts.append(reply)
            confidences.append(confidence)
            human_attributes.append(human_attr)
            bot_attributes.append(bot_attr)
            attributes.append(attr)

        return texts, confidences, human_attributes, bot_attributes, attributes
