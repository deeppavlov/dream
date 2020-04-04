import sentry_sdk
import random
import requests
import json
import logging
from os import getenv
from common.constants import CAN_NOT_CONTINUE, CAN_CONTINUE
from common.news import BREAKING_NEWS
from common.utils import is_yes, is_no
from common.emotion import detect_emotion


ENTITY_SERVICE_URL = getenv('COBOT_ENTITY_SERVICE_URL')
QUERY_SERVICE_URL = getenv('COBOT_QUERY_SERVICE_URL')
QA_SERVICE_URL = getenv('COBOT_QA_SERVICE_URL')
API_KEY = getenv('COBOT_API_KEY')
sentry_sdk.init(getenv('SENTRY_DSN'))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
physical_activites = ('I read that physical activities increase '
                      'your endorphins level! Have you ever heard about 7 minute workout?')
feel_better = 'Hmm… What do you think may make you feel better?'
seven_minute_descr = ('I suggest you to type 7-minute workout in youtube to see how it’s done. '
                      'It’s a short, rapid-fire series of exercises that use your own body weight. '
                      f'{BREAKING_NEWS}')
user_knows_7minute = (f"The power of this workout is that it's simple to do. {BREAKING_NEWS}")
string_surprise = 'I feel that you are surprised. But you are not the first surprised man on the Earth.' \
                  "The Shakespeare wrote: 'There are more things in heaven and earth, Horatio, " \
                  "Than are dreamt of in your philosophy.' He wrote it in 'Hamlet' four centuries ago. " \
                  "What is your favorite  Shakespeare's play?"
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
               'joy': [f'Your joy pleases me. {physical_activites}',
                       f'I am glad to see you being so happy! {physical_activites}'],
               'love': [f'Your love pleases me. {physical_activites}',
                        f'I am glad to see you being so happy! {physical_activites}'],
               'surprise': [f'Things can be really suprising. {physical_activites}', string_surprise],
               'neutral': ['']}

jokes = [joke1, joke2, joke3, joke4, joke5, joke6, joke7, joke8, joke9, joke10, joke11, joke12]


def get_answer(phrase):
    headers = {'Content-Type': 'application/json;charset=utf-8', 'x-api-key': API_KEY}
    answer = requests.request(url=QA_SERVICE_URL, headers=headers, timeout=2,
                              data=json.dumps({'question': phrase}), method='POST').json()
    return answer['response']


class EmotionSkillScenario:
    def __init__(self):
        self.precision = {'anger': 1, 'fear': 0.894, 'joy': 1,
                          'love': 0.778, 'sadness': 1, 'surprise': 0.745, 'neutral': 0}

    def _get_user_emotion(self, annotated_user_phrase):
        most_likely_emotion = None
        emotion_probs = annotated_user_phrase['annotations']['emotion_classification']['text']
        most_likely_prob = max(emotion_probs.values())
        for emotion in emotion_probs.keys():
            if emotion_probs[emotion] == most_likely_prob:
                most_likely_emotion = emotion
        return most_likely_emotion

    def _check_for_repetition(self, reply, prev_replies_for_user):
        reply = reply.lower()
        lower_news = BREAKING_NEWS.lower()
        lower_physical = physical_activites.lower()
        if reply in prev_replies_for_user:
            return True
        for prev_reply in prev_replies_for_user:
            if lower_news in prev_reply and lower_news in reply:
                return True
            if lower_physical in prev_reply and lower_physical in reply:
                return True
        return False

    def _get_reply_and_confidence(self, prev_bot_phrase, intent, most_likely_emotion):
        is_joke_state = 'can i tell you a joke' in prev_bot_phrase
        is_feel_better_now_state = 'do you feel better now' in prev_bot_phrase
        is_what_make_feel_better_state = 'may make you feel better' in prev_bot_phrase
        is_heard_7_minute_state = 'heard about 7 minute workout' in prev_bot_phrase

        reply, confidence = "", 0
        if intent == 'yes':
            if is_joke_state:
                reply, confidence = random.choice(jokes), 1.0
                reply += '. Do you feel better now?'
            elif is_feel_better_now_state:
                reply = physical_activites
                confidence = 1.0
            elif is_what_make_feel_better_state:
                reply = physical_activites
                confidence = 1.0
            elif is_heard_7_minute_state:
                reply = user_knows_7minute
                confidence = 1.0
        elif intent == 'no':
            if is_joke_state or is_feel_better_now_state:
                reply, confidence = feel_better, 1.0
            elif is_what_make_feel_better_state:
                reply = physical_activites
                confidence = 1.0
            elif is_heard_7_minute_state:
                reply = seven_minute_descr
                confidence = 1.0
        else:
            if is_what_make_feel_better_state:
                reply = physical_activites
                confidence = 1.0
        logger.info(f"_get_reply_and_confidence {prev_bot_phrase}; {intent}; {most_likely_emotion};"
                    f" reply: {reply}")
        return reply, confidence

    def __call__(self, dialogs):
        texts = []
        confidences = []
        attrs = []
        for dialog in dialogs:
            try:
                attr = {"can_continue": CAN_CONTINUE}
                annotated_user_phrase = dialog['utterances'][-1]
                most_likely_emotion = self._get_user_emotion(annotated_user_phrase)
                prev_replies_for_user = [u['text'].lower() for u in dialog['bot_utterances']]
                prev_bot_phrase = ''
                if prev_replies_for_user:
                    prev_bot_phrase = prev_replies_for_user[-1]

                logger.info(f"user sent: {annotated_user_phrase['text']}")
                if is_yes(annotated_user_phrase):
                    reply, confidence = self._get_reply_and_confidence(prev_bot_phrase, 'yes', most_likely_emotion)
                elif is_no(annotated_user_phrase):
                    reply, confidence = self._get_reply_and_confidence(prev_bot_phrase, 'no', most_likely_emotion)
                else:
                    reply, confidence = self._get_reply_and_confidence(prev_bot_phrase, 'other', most_likely_emotion)
                    if not reply and most_likely_emotion:
                        reply = random.choice(phrase_dict[most_likely_emotion])
                        confidence = min(0.98, self.precision[most_likely_emotion])
                        if len(dialog['utterances']) > 1:
                            if detect_emotion(dialog['utterances'][-2], annotated_user_phrase):
                                confidence = 1.0
                        logger.info(f"__call__ reply: {reply}; conf: {confidence};"
                                    f" user_phrase: {annotated_user_phrase['text']}")
            except Exception as e:
                logger.exception("exception in emotion skill")
                sentry_sdk.capture_exception(e)
                reply = ""
                confidence = 0

            if reply and self._check_for_repetition(reply, prev_replies_for_user):
                confidence = 0.95
            if not reply or confidence == 0:
                attr['can_continue'] = CAN_NOT_CONTINUE
            texts.append(reply)
            confidences.append(confidence)
            attrs.append(attr)

        return texts, confidences, attrs  # , human_attributes, bot_attributes, attributes
