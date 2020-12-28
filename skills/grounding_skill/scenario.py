import sentry_sdk
import logging
from os import getenv
from common.grounding import what_we_talk_about
from collections import defaultdict

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
            human_attr = {}
            bot_attr = dialog["bot"]["attributes"]
            bot_attr["used_links"] = bot_attr.get("used_links", defaultdict(list))
            attr = {}
            try:
                if not what_we_talk_about(dialog['utterances'][-1]):
                    reply, confidence = '', 0
                elif len(dialog.get('human_utterances', [])) < 2:
                    reply, confidence = DONTKNOW_PHRASE, DONTKNOW_CONF
                else:
                    prev_annotations = dialog['human_utterances'][-2].get('annotations', dict())
                    logger.debug('Running grounding skill')
                    reply = 'To my understanding, we are talking about '
                    if 'cobot_dialogact' in prev_annotations:  # Support different formats
                        prev_annotations['cobot_dialogact_topics'] = prev_annotations['cobot_dialogact'].get('topics',
                                                                                                             [])
                        prev_annotations['cobot_dialogact_intents'] = prev_annotations['cobot_dialogact'].get('intents',
                                                                                                              [])

                    entity_list = []
                    for tmp in prev_annotations.get('ner', []):
                        if len(tmp) > 0 and 'text' in tmp[0]:
                            entity_list.append(tmp[0]['text'])
                    my_entities = ', '.join([str(k) for k in sorted(entity_list)])

                    topic_list1 = prev_annotations.get('cobot_topics', [])
                    if 'text' in topic_list1:
                        topic_list1 = topic_list1['text']
                    topic_list2 = prev_annotations.get('cobot_dialogact_topics', [])
                    if 'text' in topic_list2:
                        topic_list2 = topic_list2['text']

                    topic_list = topic_list1 + topic_list2

                    topic_list = list(set(topic_list))
                    topic_list = [j.replace('_', ' ') for j in topic_list if j not in ['Other', 'Phatic']]
                    my_topics = ', '.join([str(k) for k in sorted(topic_list)])

                    intent_list = prev_annotations.get('cobot_dialogact_intents', [])
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
