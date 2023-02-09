import sentry_sdk
import random
import logging
from os import getenv
from common.constants import MUST_CONTINUE, CAN_CONTINUE_SCENARIO
from common.link import link_to, LIST_OF_SCRIPTED_TOPICS, skills_phrases_map
from common.emotion import (
    is_joke_requested,
    is_sad,
    is_alone,
    is_boring,
    skill_trigger_phrases,
    talk_about_emotion,
    is_pain,
    emo_advice_requested,
    is_positive_regexp_based,
)
from common.universal_templates import book_movie_music_found
from common.utils import get_emotions, is_yes, is_no
from common.greeting import HOW_ARE_YOU_RESPONSES
from collections import defaultdict
import re

sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

LANGUAGE = getenv("LANGUAGE", "EN")

SCRIPTED_TRIGGER_PHRASES = []
for skill in LIST_OF_SCRIPTED_TOPICS:
    SCRIPTED_TRIGGER_PHRASES.extend(list(skills_phrases_map[skill]))


class EmotionSkillScenario:
    def __init__(self, steps, jokes, advices, logger):
        self.emotion_precision = {
            "anger": 0.9,
            "fear": 0.8,
            "joy": 0.8,
            "disgust": 0.8,
            "sadness": 0.98,
            "surprise": 0.8,
            "neutral": 0,
        }
        self.emotion_thresholds = {
            "anger": 0.99999,
            "fear": 0.5,
            "joy": 0.5,
            "disgust": 0.5,
            "sadness": 0.6,
            "surprise": 0.5,
            "neutral": 0.5,
        }
        self.steps = steps
        self.jokes = jokes
        self.advices = advices
        self.logger = logger
        self.regexp_sad = False

    def _get_user_emotion(self, annotated_user_phrase, discard_emotion=None):
        if any([is_sad(annotated_user_phrase), is_alone(annotated_user_phrase)]):
            self.regexp_sad = True
            logger.info(f"Sadness detected by regexp in {annotated_user_phrase['text']}")
            return "sadness"

        most_likely_emotion = "neutral"
        emotion_probs = get_emotions(annotated_user_phrase, probs=True)
        if discard_emotion in emotion_probs:
            emotion_probs.pop(discard_emotion)
        most_likely_prob = max(emotion_probs.values())
        for emotion in emotion_probs.keys():
            if (
                emotion_probs.get(emotion, 0) == most_likely_prob
                and emotion_probs.get(emotion, 0) >= self.emotion_thresholds[emotion]
            ):
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
        result = result or "how do you feel" in bot_phrase
        result = result or "how are you" in bot_phrase
        return result

    def _random_choice(self, data, discard_data=None):
        discard_data = [] if discard_data is None else discard_data
        chosen_data = list(set(data).difference(set(discard_data)))
        if len(chosen_data):
            return random.choice(chosen_data)
        else:
            return ""

    # def _is_stop()

    def _get_reply_and_conf(self, annotated_user_phrase, bot_phrase, emotion, emotion_skill_attributes, human_attr):
        user_phrase = annotated_user_phrase["text"]

        is_yes_detected = is_yes(annotated_user_phrase)
        is_no_detected = is_no(annotated_user_phrase)
        start_states = {
            "joy": "joy_i_feel" if self._check_i_feel(user_phrase, bot_phrase) else "joy_feeling_towards_smth",
            "sadness": "sad_and_lonely",
            "fear": "fear",
            "anger": "anger",
            "surprise": "surprise",
            "disgust": "disgust",
        }
        if "emotion_skill" not in human_attr:
            human_attr["emotion_skill"] = {}
        if emotion != "neutral":
            human_attr["emotion_skill"]["last_emotion"] = emotion
        state = emotion_skill_attributes.get("state", "")
        prev_jokes_advices = emotion_skill_attributes.get("prev_jokes_advices", [])

        just_asked_about_jokes = "why hearing jokes is so important for you? are you sad?" in bot_phrase
        reply, confidence = "", 0
        link = ""
        self.logger.info(
            f"_get_reply_and_conf {user_phrase}; {bot_phrase}; {emotion}; {just_asked_about_jokes};"
            f" {emotion_skill_attributes}; {is_yes_detected}; {is_no_detected}; {human_attr}"
        )

        if state == "":
            # start_state
            state = start_states[emotion]
            step = self.steps[state]
            reply = self._random_choice(step["answers"])
            confidence = min(0.98, self.emotion_precision[emotion])
            if len(step["next_step"]):
                state = random.choice(step["next_step"])
        elif state == "sad_and_lonely" and just_asked_about_jokes and is_no:
            reply = "Actually, I love jokes but not now. Dead serious about that."
            confidence = 0.99
            state = ""
        elif state == "offered_advice":
            # we offered an advice
            if is_no_detected or is_positive_regexp_based({"text": user_phrase}):
                state = "no"
                step = self.steps[state]
                reply = random.choice(step["answers"])
                if len(step["next_step"]):
                    state = random.choice(step["next_step"])
                else:
                    state = ""
                confidence = 0.8
            else:
                # provide advices and offer another one
                reply = self._random_choice(self.advices[emotion], prev_jokes_advices)
                state = "offer_another_advice"
                if reply == "":
                    state = "sad_and_lonely_end"
                    step = self.steps[state]
                    reply = random.choice(step["answers"])
                else:
                    prev_jokes_advices.append(reply)
                    if len(prev_jokes_advices) == len(self.advices[emotion]):
                        state = "sad_and_lonely_end"
                confidence = 1.0 if is_yes else 0.8
        else:
            if emotion in ["sadness", "fear", "anger"] and "joy" in state:
                state = "sad_and_lonely"
            step = self.steps[state]
            reply = random.choice(step["answers"])
            if len(step["next_step"]):
                state = random.choice(step["next_step"])
            if state == "offer_advice" and sorted(self.advices.get(emotion, [])) == sorted(prev_jokes_advices):
                logger.warning("Asked for advice, but we have already done them")
                reply, confidence = "", 0
            link = step["link"]
            if link:
                link = link_to([link], human_attributes=human_attr)
                link["phrase"] = reply
                # reply += link['phrase']
            confidence = 0.8

        emotion_skill_attributes = {"state": state, "emotion": emotion, "prev_jokes_advices": prev_jokes_advices}
        if "joy" in state:
            confidence = confidence * 0.5
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
                    "emotion_skill_attributes", {}
                )
                emotion_skill_attributes = human_attributes["emotion_skill_attributes"]
                state = emotion_skill_attributes.get("state", "")
                emotion = emotion_skill_attributes.get("emotion", "")
                last_emotion = emotion_skill_attributes.get("last_emotion", "neutral")
                bot_attributes = {}
                attr = {"can_continue": CAN_CONTINUE_SCENARIO}
                annotated_user_phrase = dialog["human_utterances"][-1]
                # user_phrase = annotated_user_phrase['text']
                most_likely_emotion = self._get_user_emotion(annotated_user_phrase)
                prev_bot_phrase, prev_annotated_bot_phrase = "", {}
                if dialog["bot_utterances"]:
                    prev_annotated_bot_phrase = dialog["bot_utterances"][-1]
                    prev_bot_phrase = prev_annotated_bot_phrase["text"]
                very_confident = any(
                    [
                        function(annotated_user_phrase)
                        for function in [is_sad, is_boring, is_alone, is_joke_requested, is_pain]
                    ]
                )
                very_very_confident = very_confident and any(
                    [
                        how_are_you_response.lower() in prev_bot_phrase.lower()
                        for how_are_you_response in HOW_ARE_YOU_RESPONSES[LANGUAGE]
                    ]
                )
                # Confident if regezp
                link = ""
                if len(dialog["bot_utterances"]) >= 1:
                    # Check if we were interrupted
                    active_skill = dialog["bot_utterances"][-1]["active_skill"] == "emotion_skill"
                    if not active_skill and state != "":
                        state = ""
                        emotion_skill_attributes["state"] = ""
                if emotion == "" or state == "":
                    emotion = most_likely_emotion
                if is_joke_requested(annotated_user_phrase):
                    state = "joke_requested"
                    emotion_skill_attributes["state"] = state
                elif is_pain(annotated_user_phrase):
                    state = "pain_i_feel"
                    emotion_skill_attributes["state"] = state
                elif emo_advice_requested(annotated_user_phrase["text"]):
                    if emotion == "neutral" and last_emotion != "neutral":
                        emotion = last_emotion
                    if emotion == "neutral":
                        state = "offer_advice"
                    else:
                        reply, confidence, state = "How do you feel?", 0.95, ""
                logger.info(f"user sent: {annotated_user_phrase['text']} state: {state} emotion: {emotion}")
                if talk_about_emotion(annotated_user_phrase, prev_annotated_bot_phrase):
                    reply = f"OK. {random.choice(skill_trigger_phrases())}"
                    attr["can_continue"] = MUST_CONTINUE
                    confidence = 1.0
                elif emotion != "neutral" or state != "":
                    reply, confidence, link, emotion_skill_attributes = self._get_reply_and_conf(
                        annotated_user_phrase, prev_bot_phrase, emotion, emotion_skill_attributes, human_attributes
                    )
                    human_attributes["emotion_skill_attributes"] = emotion_skill_attributes
                    if book_movie_music_found(annotated_user_phrase):
                        logging.info("Found named topic in user utterance - dropping confidence")
                        confidence = min(confidence, 0.9)
                else:
                    reply = ""
                    confidence = 0.0
                was_trigger = any([trigger_question in prev_bot_phrase for trigger_question in skill_trigger_phrases()])
                was_scripted_trigger = any(
                    [trigger_phrase in prev_bot_phrase for trigger_phrase in SCRIPTED_TRIGGER_PHRASES]
                )
                if dialog["bot_utterances"]:
                    was_active = dialog["bot_utterances"][-1].get("active_skill", "") == "emotion_skill"
                    was_scripted = dialog["bot_utterances"][-1].get("active_skill", "") in LIST_OF_SCRIPTED_TOPICS
                else:
                    was_active = False
                    was_scripted = False
                if (was_trigger or was_active or self.regexp_sad) and not was_scripted:
                    attr["can_continue"] = CAN_CONTINUE_SCENARIO
                    confidence = 0.99
                elif not very_very_confident and not was_active:
                    confidence = min(confidence, 0.99)
                    attr["can_continue"] = CAN_CONTINUE_SCENARIO
                elif state != "joke_requested":
                    if was_scripted or reply == dialog["bot_utterances"][-1] or was_scripted_trigger:
                        confidence = 0.5 * confidence
            except Exception as e:
                self.logger.exception("exception in emotion skill")
                sentry_sdk.capture_exception(e)
                reply = ""
                state = ""
                confidence = 0.0
                human_attributes, bot_attributes, attr = {}, {}, {}
                link = ""
                annotated_user_phrase = {"text": ""}

            if link and "skill" in link:
                if link["skill"] not in human_attributes["used_links"]:
                    human_attributes["used_links"][link["skill"]] = []
                human_attributes["used_links"][link["skill"]].append(link["phrase"])

            self.logger.info(
                f"__call__ reply: {reply}; conf: {confidence};"
                f" user_phrase: {annotated_user_phrase['text']}"
                f" human_attributes: {human_attributes}"
                f" bot_attributes: {bot_attributes}"
                f" attributes: {attr}"
            )
            texts.append(reply)
            confidences.append(confidence)
            human_attrs.append(human_attributes)
            bot_attrs.append(bot_attributes)
            attrs.append(attr)

        return texts, confidences, human_attrs, bot_attrs, attrs
