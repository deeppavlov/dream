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
DONTKNOW_PHRASE = "Seems like I have no idea what we are talking about."


def get_intent_dict(entity_name):
    #  order DOES matter
    intent_dict = {'Information_DeliveryIntent': f'You just told me about {entity_name}, right?',
                   'Information_RequestIntent': f"You've asked me about {entity_name} haven't you?",
                   'User_InstructionIntent': "You just gave me a command. Am I right?",
                   "Opinion_ExpressionIntent": f"You just shared your opinion about {entity_name} with me, right?",
                   "ClarificationIntent": f"You clarified me what you've just said about {entity_name}, right?",
                   "Topic_SwitchIntent": "You wanted to change topic, right?",
                   "Opinion_RequestIntent": f"You wanted to hear my thoughts about {entity_name}, am I correct?"}
    return intent_dict


def get_da_topic_dict():
    #  order DOES matter
    topic_dict = {"Entertainment_Movies": "We were discussing movies, am I right?",
                  "Entertainment_Books": "We were discussing books, am I right?",
                  'Entertainment_General': "We are just trying to be polite to each other, aren't we?",
                  "Science_and_Technology": "I was under impression we were chatting about technology stuff",
                  "Sports": "So I thought we were talking about sports",
                  "Politics": "Correct me if I'm wrong but I thought we were discussing politics"}
    return topic_dict


def get_cobot_topic_dict():
    #  order DOES matter
    topic_dict = {'Phatic': "We are just trying to be polite to each other, aren't we?",
                  "Other": "I can't figure out what we are talking about exactly. Can you spare a hand?",
                  "Movies_TV": "We were discussing movies, am I right?",
                  "Music": "Thought we were talking about music",
                  "SciTech": "I was under impression we were chatting about technology stuff",
                  "Literature": "We were discussing literature, am I right?",
                  "Travel_Geo": "Thought we were talking about some travel stuff",
                  "Celebrities": "We're discussing celebrities, right?",
                  "Games": "We're talking about games, correct?",
                  "Pets_Animals": "Thought we were talking about animals",
                  "Sports": "So I thought we were talking about sports",
                  "Psychology": "Correct me if I'm wrong but I thought we were talking about psychology",
                  "Religion": "Aren't we talking about religion, my dear?",
                  "Weather_Time": "Aren't we discussing the best topic of all times, weather?",
                  "Food_Drink": "Thought we were discussing food stuff",
                  "Politics": "Correct me if I'm wrong but I thought we were discussing politics",
                  "Sex_Profanity": "This is a something I'd rather avoid talking about",
                  "Art_Event": "My understanding is we are discussing arts, aren't we?",
                  "Math": "My guess is we were talking about math stuff",
                  "News": "Aren't we discussing news my dear friend?",
                  "Entertainment": "Thought we were discussing something about entertainment",
                  "Fashion": "We are talking about fashion am I right?"}
    return topic_dict


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
            texts.append(reply)
            confidences.append(confidence)
            human_attributes.append(human_attr)
            bot_attributes.append(bot_attr)
            attributes.append(attr)

        return texts, confidences, human_attributes, bot_attributes, attributes
