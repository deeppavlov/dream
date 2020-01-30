import sentry_sdk
import random
import requests
import json
import logging
from os import getenv
from string import punctuation


#  import os
#  import zipfile
#  import _pickle as cPickle


def is_no(annotated_phrase):
    y1 = annotated_phrase['annotations']['intent_catcher'].get('no', {}).get('detected') == 1
    user_phrase = annotated_phrase['text']
    user_phrase = user_phrase.replace("n't", ' not ')
    for sign in punctuation:
        user_phrase = user_phrase.replace(sign, ' ')
    y2 = ' no ' in user_phrase or ' not ' in user_phrase
    return y1 or y2


ENTITY_SERVICE_URL = getenv('COBOT_ENTITY_SERVICE_URL')
QUERY_SERVICE_URL = getenv('COBOT_QUERY_SERVICE_URL')
QA_SERVICE_URL = getenv('COBOT_QA_SERVICE_URL')
API_KEY = getenv('COBOT_API_KEY')
sentry_sdk.init(getenv('SENTRY_DSN'))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
phrase_dict = {'excited': "I am glad to see that you feel so good.",
               'joyful': 'I am glad to see that you feel so good.',
               'content': 'I am glad to see that you feel so good.',
               'grateful': 'I am glad to see that you feel so good',
               'apprehensive': 'Be careful but not full of care.',
               'caring': 'Be careful but not full of care.',
               'prepared': 'Be careful but not full of care.',
               'anticipating': 'Be careful but not full of care.',
               'proud': 'I hope you will have even more reasons to feel so proud.',
               'nostalgic': 'I believe things will be even better than they were.',
               'sad': "Please, calm down and cheer up. Can I tell you a joke?",
               'afraid': "Please, calm down and cheer up. Can I tell you a joke?",
               'anxious': "Please, calm down and cheer up. Can I tell you a joke?",
               'embarrassed': "Please, calm down and cheer up. Can I tell you a joke?",
               'devastated': "Please, calm down and cheer up. Can I tell you a joke?",
               'ashamed': "Please, calm down and cheer up. Can I tell you a joke?",
               'disappointed': "Please, calm down and cheer up. Can I tell you a joke?",
               'guilty': "Please, calm down and cheer up. Can I tell you a joke?",
               'angry': "Please, calm down and cheer up. Can I tell you a joke?",
               'annoyed': "Please, calm down and cheer up. Can I tell you a joke?",
               'furious': "Please, calm down and cheer up. Can I tell you a joke?",
               'disgusted': "Please, calm down and cheer up. Can I tell you a joke?",
               'lonely': "Long loneliness is better than bad company.",
               'surprised': 'I am glad to impress you.',
               'impressed': 'I am glad to impress you.',
               'terrified': 'I am glad to impress you.',
               'context': '',
               'jealous': 'Envy shoots at others and wounds itself.',
               'hopeful': 'Everything that is done in this world is done by hope. ',
               'trusting': 'Everything that is done in this world is done by hope. ',
               'confident': 'Everything that is done in this world is done by hope. ',
               'faithful': 'Everything that is done in this world is done by hope. '}
jokes = ["When you hit a speed bump in a school zone and remember, there are no speed bumps.",
         ''.join(["Police arrested two kids yesterday, one was drinking battery acid, the other was eating fireworks."
                  "They charged one – and let the other one-off."]),
         ''.join(["Two aerials meet on a roof – fall in love – get married. "
                  "The ceremony was rubbish – but the reception was brilliant."]),
         "I went to the doctors the other day, and I said, ‘Have you got anything for wind?’ So he gave me a kite. ",
         "There’s two fish in a tank, and one says How do you drive this thing?",
         "A sandwich walks into a bar. The barman says sorry we don’t serve food in here ",
         " Went to the paper shop – it had blown away.",
         " I tried water polo, but my horse drowned. ",
         ''.join([" I’ll tell you what I love doing more than anything: trying to pack myself in a small suitcase.",
                  "I can hardly contain myself. "]),
         ''.join(["A three-legged dog walks into a saloon in the Old West.",
                  "He slides up to the bar and announces: I’m looking for the man who shot my paw. "]),
         ''.join(["Two Eskimos sitting in a kayak were chilly.",
                  "But when they lit a fire in the craft, it sank, proving once and for all, "
                  "that you can’t have your kayak and heat it. "]),
         "A priest, a rabbi and a vicar walk into a bar. The barman says, Is this some kind of joke?",
         "A jump-lead walks into a bar. The barman says I’ll serve you, but don’t start anything",
         "My therapist says I have a preoccupation with vengeance. We’ll see about that."]


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

    def __call__(self, dialogs):
        texts = []
        confidences = []
        for dialog in dialogs:
            try:
                logging.info(dialog)
                text_utterances = [j['text'] for j in dialog['utterances']]
                bot_phrases = [j for i, j in enumerate(text_utterances) if i % 2 == 1]
                annotated_user_phrase = dialog['utterances'][-1]
                emotion_probs = ['annotations']['emotion_classification']['text']
                emo_groups = [['sad', 'afraid', 'anxious', 'embarrassed', 'devastated', 'ashamed',
                               'disappointed', 'guilty', 'angry', 'annoyed', 'furious', 'disgusted'],
                              ['surprised', 'impressed', 'terrified'],
                              ['excited', 'joyful', 'grateful', 'content'],
                              ['apprehensive', 'caring', 'prepared', 'anticipating'],
                              ['trusting', 'confident', 'faithful', 'hopeful']]  # Groups of synonymous emotions

                for emo_group in emo_groups:
                    sum_group_prob = sum([emotion_probs[emotion] for emotion in emo_group]) / len(emo_group)
                    for emotion in emo_group:
                        emotion_probs[emotion] = sum_group_prob + 0.01 * emotion_probs[emotion]
                        emotion_probs[emotion] = min(emotion_probs[emotion], self.conf_sure)
                most_likely_prob = max(emotion_probs.values())
                for emotion in emotion_probs.keys():
                    if emotion_probs[emotion] == most_likely_prob:
                        most_likely_emotion = emotion
                if 'Can I tell you a joke' in bot_phrases[-1] and not is_no(annotated_user_phrase):
                    reply, confidence = random.choice(jokes), self.conf_sure
                else:
                    reply, confidence = phrase_dict[most_likely_emotion], most_likely_prob
                if 'Can I tell you a joke' in reply and confidence < self.conf_sure:
                    # Push reply with offering a joke forward
                    confidence = self.conf_sure
            except Exception as e:
                logger.exception("exception in emotion skill")
                sentry_sdk.capture_exception(e)
                reply = "sorry"
                confidence = 0
            texts.append(reply)
            confidences.append(confidence)

        return texts, confidences  # , human_attributes, bot_attributes, attributes
