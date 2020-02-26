import sentry_sdk
import random
import requests
import json
import logging
from os import getenv
from string import punctuation
from common.constants import CAN_NOT_CONTINUE, CAN_CONTINUE

#  import os
#  import zipfile
#  import _pickle as cPickle


def is_yes(annotated_phrase):
    y1 = annotated_phrase['annotations']['intent_catcher'].get('yes', {}).get('detected') == 1
    user_phrase = annotated_phrase['text']
    for sign in punctuation:
        user_phrase = user_phrase.replace(sign, ' ')
    y2 = ' yes ' in user_phrase
    return y1 or y2


ENTITY_SERVICE_URL = getenv('COBOT_ENTITY_SERVICE_URL')
QUERY_SERVICE_URL = getenv('COBOT_QUERY_SERVICE_URL')
QA_SERVICE_URL = getenv('COBOT_QA_SERVICE_URL')
API_KEY = getenv('COBOT_API_KEY')
sentry_sdk.init(getenv('SENTRY_DSN'))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
string_surprise = 'I feel that you are surprised. But you are not the first surprised man on the Earth.' \
                  "The Shakespeare wrote: 'There are more things in heaven and earth, Horatio, " \
                  "Than are dreamt of in your philosophy.' He wrote it in 'Hamlet' four centuries ago."
string_fear = "Fear does not empty tomorrow of its sadness, it empties today of its power. Can I tell you a joke?"
joke1 = "When you hit a speed bump in a school zone and remember, there are no speed bumps."
joke2 = "Police arrested two kids yesterday, one was drinking battery acid, the other was eating fireworks." \
        "They charged one – and let the other one-off."
joke3 = "What do you get when you wake up on a workday and realize you ran out of coffee? A depresso."
joke4 = "I went to the doctors the other day, and I said, 'Have you got anything for wind?' So he gave me a kite. "
joke5 = "A jump-lead walks into a bar. The barman says 'I’ll serve you, but don’t start anything.'"
joke6 = "A priest, a rabbi and a vicar walk into a bar. The barman says, Is this some kind of joke?"
joke7 = "My therapist says I have a preoccupation with vengeance. We'll see about that."
joke8 = "Two Eskimos sitting in a kayak were chilly." \
        "But when they lit a fire in the craft, it sank, proving once and for all, " \
        "that you can’t have your kayak and heat it. "
joke9 = "I'll tell you what I love doing more than anything: trying to pack myself in a small suitcase." \
        "I can hardly contain myself. "
joke10 = "A three-legged dog walks into a saloon in the Old West." \
         "He slides up to the bar and announces: I'm looking for the man who shot my paw. "
joke11 = "A sandwich walks into a bar. The barman says sorry we don’t serve food in here ."
joke12 = "There’s two fish in a tank, and one says How do you drive this thing?"
phrase_dict = {'anger': ["Please, calm down. Can I tell you a joke?",
                         "I feel your pain. Can I tell you a joke?",
                         "I am ready to support you. Can I tell you a joke?"],
               'fear': ["Please, calm down. Can I tell you a joke?",
                        'It is better to face danger once than be always in fear. Can I tell you a joke?',
                        string_fear],
               'sadness': ["Please, cheer up. Can I tell you a joke?",
                           "You cannot prevent the birds of sadness from passing over your head, " + (
                               "but you can prevent them from nesting in your hair. Can I tell you a joke?"),
                           "I feel your pain. Can I tell you a joke?"],
               'joy': ['Your joy pleases me', 'Have a good time!', 'I am glad to see you being so happy!'],
               'love': ['Your love pleases me', 'Have a good time!', 'I am glad to see you being so happy!'],
               'surprise': ['Things can be really shocking.', string_surprise],
               'neutral': ['']}

jokes = [joke1, joke2, joke3, joke4, joke5, joke6, joke7, joke8, joke9, joke10, joke11, joke12]


def get_answer(phrase):
    headers = {'Content-Type': 'application/json;charset=utf-8', 'x-api-key': API_KEY}
    answer = requests.request(url=QA_SERVICE_URL, headers=headers, timeout=2,
                              data=json.dumps({'question': phrase}), method='POST').json()
    return answer['response']


class EmotionSkillScenario:

    def __init__(self):
        global phrase_dict
        self.conf_unsure = 0.5
        self.conf_sure = 0.9
        self.default_reply = "I don't know what to answer"
        self.genre_prob = 0.5
        self.phrase_dict = phrase_dict
        self.precision = {'anger': 1, 'fear': 0.894, 'joy': 1,
                          'love': 0.778, 'sadness': 1, 'surprise': 0.745, 'neutral': 0}

    def __call__(self, dialogs):
        texts = []
        confidences = []
        attrs = []
        for dialog in dialogs:
            try:
                attr = {"can_continue": CAN_NOT_CONTINUE}
                text_utterances = [j['text'] for j in dialog['utterances']]
                bot_phrases = [j for i, j in enumerate(text_utterances) if i % 2 == 1]
                if len(bot_phrases) == 0:
                    bot_phrases.append('')
                if any([j in bot_phrases[-1].lower() for j in ['how are you']]):
                    conf_sure = 0.95
                else:
                    conf_sure = self.conf_sure
                annotated_user_phrase = dialog['utterances'][-1]
                emotion_probs = annotated_user_phrase['annotations']['emotion_classification']['text']
                most_likely_prob = max(emotion_probs.values())
                most_likely_emotion = None
                for emotion in emotion_probs.keys():
                    if emotion_probs[emotion] == most_likely_prob:
                        most_likely_emotion = emotion
                assert most_likely_emotion is not None
                if 'Can I tell you a joke' in bot_phrases[-1]:
                    if is_yes(annotated_user_phrase):
                        attr["can_continue"] = CAN_CONTINUE
                        reply, confidence = random.choice(jokes), 1.0
                    else:
                        reply, confidence = '', 0
                else:
                    reply = random.choice(phrase_dict[most_likely_emotion])
                    confidence = most_likely_prob * self.precision[emotion]
                if 'Can I tell you a joke' in reply and confidence < conf_sure:
                    attr["can_continue"] = CAN_CONTINUE
                    # Push reply with offering a joke forward
                    confidence = conf_sure
            except Exception as e:
                logger.exception("exception in emotion skill")
                sentry_sdk.capture_exception(e)
                reply = "sorry"
                confidence = 0
            texts.append(reply)
            confidences.append(confidence)
            attrs.append(attr)

        return texts, confidences, attrs  # , human_attributes, bot_attributes, attributes
