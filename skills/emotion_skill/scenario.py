import sentry_sdk
import random
import logging
from os import getenv
from common.constants import MUST_CONTINUE, CAN_CONTINUE_SCENARIO
from common.link import link_to
from common.emotion import is_joke_requested, is_sad
from common.universal_templates import book_movie_music_found
from common.utils import get_emotions
from collections import defaultdict
import re


sentry_sdk.init(getenv('SENTRY_DSN'))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


class EmotionSkillScenario:
    def __init__(self, steps, jokes, advices, logger):
        self.emotion_precision = {'anger': 1, 'fear': 0.894, 'joy': 1,
                                  'love': 0.778, 'sadness': 1, 'surprise': 0.745, 'neutral': 0}
        self.steps = steps
        self.jokes = jokes
        self.advices = advices
        self.logger = logger

    def _get_user_emotion(self, annotated_user_phrase, discard_emotion=None):
        if is_sad(annotated_user_phrase['text']):
            return 'sadness'
        most_likely_emotion = None
        emotion_probs = get_emotions(annotated_user_phrase, probs=True)
        if discard_emotion in emotion_probs:
            emotion_probs.pop(discard_emotion)
        most_likely_prob = max(emotion_probs.values())
        for emotion in emotion_probs.keys():
            if emotion_probs.get(emotion, 0) == most_likely_prob:
                most_likely_emotion = emotion
        return most_likely_emotion

    # def _check_for_repetition(self, reply, prev_replies_for_user):
    #     reply = reply.lower()
    #     lower_physical = physical_activites.lower()
    #     if reply in prev_replies_for_user:
    #         return True
    #     for prev_reply in prev_replies_for_user:
    #         if lower_physical in prev_reply and lower_physical in reply:
    #             return True
    #     return False

    def _check_i_feel(self, user_phrase, bot_phrase):
        result = bool(re.match("i ((feel)|(am feeling)|(am)) .*", user_phrase))
        result = result or 'how do you feel' in bot_phrase
        result = result or 'how are you' in bot_phrase
        return result

    def _random_choice(self, data, discard_data=[]):
        chosen_data = list(set(data).difference(set(discard_data)))
        if len(chosen_data):
            return random.choice(chosen_data)
        else:
            return ""
    # def _is_stop()

    def _get_reply_and_conf(self, user_phrase, bot_phrase, emotion,
                            emotion_skill_attributes, intent, human_attr):

        start_states = {
            "joy": 'joy_i_feel' if self._check_i_feel(user_phrase, bot_phrase)
            else 'joy_feeling_towards_smth',
            "sadness": 'sadness_i_feel' if self._check_i_feel(user_phrase, bot_phrase)
            else 'sadness_feeling_towards_smth',
            "fear": 'fear',
            "anger": 'anger',
            "surprise": 'surprise',
            "love": 'love'
        }

        state = emotion_skill_attributes.get("state", "")
        if is_joke_requested(user_phrase):
            state = "joke_requested"
        prev_jokes_advices = emotion_skill_attributes.get("prev_jokes_advices", [])
        is_yes = intent.get("yes", {}).get("detected", 0)
        is_no = intent.get("no", {}).get("detected", 0)
        reply, confidence = "", 0
        link = ''
        self.logger.info(
            f"_get_reply_and_conf {user_phrase}; {bot_phrase}; {emotion};"
            f" {emotion_skill_attributes}; {intent}; {human_attr}"
        )

        if state == "":
            # start_state
            state = start_states[emotion]
            step = self.steps[state]
            reply = self._random_choice(step['answers'])
            confidence = min(0.98, self.emotion_precision[emotion])
            if len(step['next_step']):
                state = random.choice(step['next_step'])
        elif state == "joke_requested":
            # got joke request
            reply = self._random_choice(self.jokes, prev_jokes_advices)
            state = 'offer_another_joke'
            if reply == "":
                state = ""  # We are run out of jokes
                reply = "I guess I am out of jokes, sorry. Do you know any good jokes?"
            else:
                # Add joke to list of already told jokes and advices
                prev_jokes_advices.append(reply)
            confidence = 1.0
        elif state == 'offered_joke':
            # we offered a joke
            if is_yes:
                # User wants a joke -> we provide a joke and then offer another one
                reply = self._random_choice(self.jokes, prev_jokes_advices)
                state = 'offer_another_joke'
                if reply == "":
                    state = ""  # We are run out of jokes
                    reply = "Well, that was the last joke of mine. Do you know any good jokes?"
                else:
                    # Add joke to list of already told jokes and advices
                    prev_jokes_advices.append(reply)
                confidence = 1.0
            elif is_no:
                # User doesn't want a joke
                if emotion in {'sadness', 'fear', 'anger', 'surprise'}:
                    state = 'offer_advice'  # We offer an advice
                else:
                    state = 'no'  # Can't offer anything
                step = self.steps[state]
                reply = random.choice(step['answers'])
                link = step['link']
                if link:
                    link = link_to([link], human_attributes=human_attr)
                    reply += link['phrase']
                if len(step['next_step']):
                    state = random.choice(step['next_step'])
                confidence = 1.0
        elif state == 'offered_advice':
            # we offered an advice
            if is_yes:
                # provide advices and offer another one
                reply = self._random_choice(self.advices[emotion], prev_jokes_advices)
                state = 'offer_another_advice'
                if reply == "":
                    state = ""  # We are run out of advices
                    reply = "I guess i am out of advices. But you can just tell me \
                        what is on your mind and I am here to listen."
                else:
                    prev_jokes_advices.append(reply)
                confidence = 1.0
            elif is_no:
                state = 'no'
                step = self.steps[state]
                reply = random.choice(step['answers'])
                if len(step['next_step']):
                    state = random.choice(step['next_step'])
                else:
                    state = ""
                confidence = 1.0
        else:
            step = self.steps[state]
            reply = random.choice(step['answers'])
            if len(step['next_step']):
                state = random.choice(step['next_step'])
            link = step['link']
            if link:
                link = link_to([link], human_attributes=human_attr)
                link['phrase'] = reply
                # reply += link['phrase']
            confidence = 1.0

        emotion_skill_attributes = {
            "state": state,
            "emotion": emotion,
            "prev_jokes_advices": prev_jokes_advices
        }

        return reply, confidence, link, emotion_skill_attributes

    def __call__(self, dialogs):
        texts = []
        confidences = []
        attrs = []
        human_attrs = []
        bot_attrs = []
        for dialog in dialogs:
            try:
                human_attributes = {}
                human_attributes["used_links"] = dialog["human"]["attributes"].get("used_links", defaultdict(list))
                human_attributes["disliked_skills"] = dialog["human"]["attributes"].get("disliked_skills", [])
                human_attributes["emotion_skill_attributes"] = dialog["human"]["attributes"].get(
                    "emotion_skill_attributes", {})
                emotion_skill_attributes = human_attributes["emotion_skill_attributes"]
                state = emotion_skill_attributes.get("state", "")
                emotion = emotion_skill_attributes.get("emotion", "")
                bot_attributes = {}
                attr = {"can_continue": CAN_CONTINUE_SCENARIO}
                annotated_user_phrase = dialog['utterances'][-1]
                most_likely_emotion = self._get_user_emotion(annotated_user_phrase)
                intent = annotated_user_phrase['annotations'].get("intent_catcher", {})
                prev_replies_for_user = [u['text'].lower() for u in dialog['bot_utterances']]
                prev_bot_phrase = ''
                link = ''
                if prev_replies_for_user:
                    prev_bot_phrase = prev_replies_for_user[-1]
                if len(dialog['utterances']) > 1:
                    # Check if we were interrupted
                    active_skill = dialog['utterances'][-2]['active_skill'] == 'emotion_skill'
                    if not active_skill and state != "":
                        state = ""
                        emotion_skill_attributes['state'] = ""
                logger.info(f"user sent: {annotated_user_phrase['text']}")
                if emotion == "" or state == "":
                    emotion = most_likely_emotion
                if emotion != "neutral" or state != "":
                    reply, confidence, link, emotion_skill_attributes = self._get_reply_and_conf(
                        annotated_user_phrase['text'],
                        prev_bot_phrase,
                        emotion,
                        emotion_skill_attributes,
                        intent,
                        human_attributes
                    )
                    human_attributes['emotion_skill_attributes'] = emotion_skill_attributes
                    if book_movie_music_found(annotated_user_phrase):
                        logging.info('Found named topic in user utterance - dropping confidence')
                        confidence = min(confidence, 0.9)
                else:
                    reply = ""
                    confidence = 0.0

            except Exception as e:
                self.logger.exception("exception in emotion skill")
                sentry_sdk.capture_exception(e)
                reply = ""
                state = ""
                confidence = 0.0
                human_attributes, bot_attributes, attr = {}, {}, {}
                link = ""
                annotated_user_phrase = {'text': ""}

            if state != "":  # Part of a script - so we must continue
                attr['can_continue'] = MUST_CONTINUE

            if link:
                if link["skill"] not in human_attributes["used_links"]:
                    human_attributes["used_links"][link["skill"]] = []
                human_attributes["used_links"][link["skill"]].append(link['phrase'])

            self.logger.info(f"__call__ reply: {reply}; conf: {confidence};"
                             f" user_phrase: {annotated_user_phrase['text']}"
                             f" human_attributes: {human_attributes}"
                             f" bot_attributes: {bot_attributes}"
                             f" attributes: {attr}")
            texts.append(reply)
            confidences.append(confidence)
            human_attrs.append(human_attributes)
            bot_attrs.append(bot_attributes)
            attrs.append(attr)

        return texts, confidences, human_attrs, bot_attrs, attrs
