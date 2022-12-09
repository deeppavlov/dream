#!/usr/bin/env python

import logging
import time
import re
from random import choice
import json

from flask import Flask, request, jsonify
from os import getenv
import sentry_sdk

from common.constants import CAN_NOT_CONTINUE, CAN_CONTINUE_SCENARIO, CAN_CONTINUE_PROMPT, MUST_CONTINUE
from common.utils import get_skill_outputs_from_dialog, get_sentiment, is_yes
from common.universal_templates import (
    if_choose_topic,
    if_switch_topic,
    if_chat_about_particular_topic,
    is_any_question_sentence_in_utterance,
    NOT_LIKE_PATTERN,
    COMPILE_NOT_WANT_TO_TALK_ABOUT_IT,
)
from topic_words import TOPIC_PATTERNS


sentry_sdk.init(getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

with open("small_talk_scripts.json", "r") as f:
    TOPIC_SCRIPTS = json.load(f)

USER_TOPIC_START_CONFIDENCE = 0.95
FOUND_WORD_START_CONFIDENCE = 0.8
BOT_TOPIC_START_CONFIDENCE = 0.9
CONTINUE_CONFIDENCE = 0.9
LONG_ANSWER_CONTINUE_CONFIDENCE = 0.95
YES_CONTINUE_CONFIDENCE = 1.0
# if let's chat about TOPIC [key-words]
NOT_SCRIPTED_TOPICS = ["depression", "life", "sex", "star wars", "donald trump", "superheroes"]


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()
    dialogs_batch = request.json["dialogs"]
    confidences = []
    responses = []
    human_attributes = []
    bot_attributes = []
    attributes = []

    for dialog in dialogs_batch:
        used_topics = dialog["human"]["attributes"].get("small_talk_topics", [])
        human_attr = {}
        bot_attr = {}
        attr = {}

        skill_outputs = get_skill_outputs_from_dialog(
            dialog["utterances"][-3:], skill_name="small_talk_skill", activated=True
        )
        if len(skill_outputs) > 0:
            # small_talk_skill was active on the previous step
            topic = skill_outputs[0].get("small_talk_topic", "")
            script_step = skill_outputs[0].get("small_talk_step", 0)
            script = skill_outputs[0].get("small_talk_script", [])
            logger.info(f"Found previous step topic: `{topic}`.")
        else:
            topic = ""
            script_step = 0
            script = []

        _, new_user_topic, new_conf = pickup_topic_and_start_small_talk(dialog)
        logger.info(
            f"From current user utterance: `{dialog['human_utterances'][-1]['text']}` "
            f"extracted topic: `{new_user_topic}`."
        )
        sentiment = get_sentiment(dialog["human_utterances"][-1], probs=False)[0]

        if (
            len(topic) > 0
            and len(script) > 0
            and (len(new_user_topic) == 0 or new_conf == FOUND_WORD_START_CONFIDENCE or new_user_topic == topic)
        ):
            # we continue dialog if new topic was not found or was found just as the key word in user sentence.
            # because we can start a conversation picking up topic with key word with small proba
            user_dont_like = NOT_LIKE_PATTERN.search(dialog["human_utterances"][-1]["text"])
            user_stop_talking = COMPILE_NOT_WANT_TO_TALK_ABOUT_IT.search(dialog["human_utterances"][-1]["text"])
            if sentiment == "negative" or user_dont_like or user_stop_talking:
                logger.info("Found negative sentiment to small talk phrase. Finish script.")
                response, confidence, attr = (
                    "",
                    0.0,
                    {
                        "can_continue": CAN_NOT_CONTINUE,
                        "small_talk_topic": "",
                        "small_talk_step": 0,
                        "small_talk_script": [],
                    },
                )
            else:
                response, confidence, attr = get_next_response_on_topic(
                    topic, dialog["human_utterances"][-1], curr_step=script_step + 1, topic_script=script
                )
            if response != "":
                logger.info(
                    f"Continue script on topic: `{topic}`.\n"
                    f"User utterance: `{dialog['human_utterances'][-1]['text']}`.\n"
                    f"Bot response: `{response}`."
                )
        else:
            logger.info("Try to extract topic from user utterance or offer if requested.")
            response, topic, confidence = pickup_topic_and_start_small_talk(dialog)
            _is_quesion = is_any_question_sentence_in_utterance(dialog["human_utterances"][-1])
            _is_lets_chat = if_chat_about_particular_topic(
                dialog["human_utterances"][-1], dialog["bot_utterances"][-1] if dialog["bot_utterances"] else {}
            )

            if len(topic) > 0 and topic not in used_topics and (not _is_quesion or _is_lets_chat):
                logger.info(
                    f"Starting script on topic: `{topic}`.\n"
                    f"User utterance: `{dialog['human_utterances'][-1]['text']}`.\n"
                    f"Bot response: `{response}`."
                )
                # topic script start, response is already formulated
                human_attr["small_talk_topics"] = used_topics + [topic]
                attr["response_parts"] = ["prompt"]
                attr["can_continue"] = CAN_CONTINUE_PROMPT
                attr["small_talk_topic"] = topic
                attr["small_talk_step"] = 0
                attr["small_talk_script"] = TOPIC_SCRIPTS.get(topic, [])
            else:
                logger.info("Can not extract or offer NEW topic.")
                response = ""

        if len(response) == 0:
            confidence = 0.0

        responses.append(response)
        confidences.append(confidence)
        human_attributes.append(human_attr)
        bot_attributes.append(bot_attr)
        attributes.append(attr)

    total_time = time.time() - st_time
    logger.info(f"small_talk_skill exec time: {total_time:.3f}s")
    return jsonify(list(zip(responses, confidences, human_attributes, bot_attributes, attributes)))


def get_next_response_on_topic(topic, curr_user_uttr, curr_step=0, topic_script=None):
    topic_script = [] if topic_script is None else topic_script
    attr = {}

    if curr_step == len(topic_script):
        # prev_bot_uttr was the last in the script
        # can not continue with the same script&topic
        logger.info("Script was finished.")
        attr["can_continue"] = CAN_NOT_CONTINUE
        attr["small_talk_topic"] = ""
        attr["small_talk_step"] = 0
        attr["small_talk_script"] = []
        return "", 0.0, attr

    if isinstance(topic_script[curr_step], str):
        next_bot_uttr = topic_script[curr_step]
        attr["can_continue"] = CAN_CONTINUE_SCENARIO
        attr["small_talk_topic"] = topic
        attr["small_talk_step"] = curr_step
        if len(curr_user_uttr["text"].split()) > 7:
            confidence = LONG_ANSWER_CONTINUE_CONFIDENCE
        else:
            confidence = CONTINUE_CONFIDENCE
    elif isinstance(topic_script[curr_step], dict):
        yes_detected = is_yes(curr_user_uttr)
        if yes_detected:
            next_bot_uttr = topic_script[curr_step]["yes"]
            attr["can_continue"] = MUST_CONTINUE
            attr["small_talk_topic"] = topic
            attr["small_talk_step"] = curr_step
            confidence = YES_CONTINUE_CONFIDENCE
        else:
            # consider all other answers as NO
            next_bot_uttr = topic_script[curr_step]["no"]
            attr["can_continue"] = CAN_CONTINUE_SCENARIO
            attr["small_talk_topic"] = topic
            attr["small_talk_step"] = curr_step
            if len(curr_user_uttr["text"].split()) > 7:
                confidence = LONG_ANSWER_CONTINUE_CONFIDENCE
            else:
                confidence = CONTINUE_CONFIDENCE
    else:
        next_bot_uttr = ""
        confidence = 0.0

    if isinstance(next_bot_uttr, list):
        if len(next_bot_uttr) == 0:
            logger.info("Script was finished.")
            attr["can_continue"] = CAN_NOT_CONTINUE
            attr["small_talk_topic"] = ""
            attr["small_talk_step"] = 0
            attr["small_talk_script"] = []
            return "", 0.0, attr
        attr["small_talk_script"] = topic_script[:curr_step] + next_bot_uttr + topic_script[curr_step + 1 :]
        next_bot_uttr = attr["small_talk_script"][curr_step]
    else:
        attr["small_talk_script"] = topic_script[:curr_step] + [next_bot_uttr] + topic_script[curr_step + 1 :]
    if attr["small_talk_step"] == len(topic_script) - 1:
        # last uttr of the script, can not continue!
        attr["can_continue"] = CAN_NOT_CONTINUE

    return next_bot_uttr, confidence, attr


def offer_topic(dialog):
    """
    There is an opportunity to choose topic taking into account the dialog history.
    For now, it's just random pick up from `TOPIC_WORDS.keys()`.

    Args:
        dialog: dialog from agent

    Returns:
        string topic out of `TOPIC_WORDS.keys()`
    """
    used_topics = dialog["human"]["attributes"].get("small_talk_topics", [])
    topic_set = (
        set(TOPIC_PATTERNS.keys())
        .difference(set(used_topics))
        .difference(
            {
                "sex",
                "me",
                "politics",
                "depression",
                "donald trump",
                "news",
                "school",
                "star wars",
                "work",
                "you",
                "family",
            }
        )
    )
    if len(topic_set) > 0:
        topic = choice(list(topic_set))
    else:
        topic = ""
    return topic


def find_topics_in_substring(substring):
    """
    Search topic words in the given string

    Args:
        substring: any string

    Returns:
        list of topics out of `TOPIC_WORDS.keys()`
    """
    topics = []
    for topic in TOPIC_PATTERNS:
        if re.search(TOPIC_PATTERNS.get(topic, "XXXXX"), substring):
            topics.append(topic)

    return topics


def which_topic_lets_chat_about(last_user_uttr, last_bot_uttr):
    for topic in TOPIC_PATTERNS:
        if if_chat_about_particular_topic(last_user_uttr, last_bot_uttr, compiled_pattern=TOPIC_PATTERNS[topic]):
            return topic
    return None


def pickup_topic_and_start_small_talk(dialog):
    """
    Pick up topic for small talk and return first response.

    Args:
        dialog: dialog from agent

    Returns:
        Tuple of (response, topic, confidence)
    """
    last_user_uttr = dialog["human_utterances"][-1]
    if len(dialog["bot_utterances"]) > 0:
        last_bot_uttr = dialog["bot_utterances"][-1]
    else:
        last_bot_uttr = {"text": "---", "annotations": {}}

    topic_user_wants_to_discuss = which_topic_lets_chat_about(last_user_uttr, last_bot_uttr)

    if if_choose_topic(last_user_uttr, last_bot_uttr) or if_switch_topic(last_user_uttr["text"].lower()):
        # user asks bot to chose topic: `pick up topic/what do you want to talk about/would you like to switch topic`
        # or bot asks user to chose topic and user says `nothing/anything/don't know`
        # if user asks to switch the topic
        topic = offer_topic(dialog)
        if topic in TOPIC_PATTERNS:
            if topic == "me":
                response = "Let's talk about you. " + TOPIC_SCRIPTS.get(topic, [""])[0]
            elif topic == "you":
                response = "Let's talk about me. " + TOPIC_SCRIPTS.get(topic, [""])[0]
            else:
                response = f"Let's talk about {topic}. " + TOPIC_SCRIPTS.get(topic, [""])[0]
            confidence = BOT_TOPIC_START_CONFIDENCE
        else:
            response = ""
            confidence = 0.0
        logger.info(f"Bot initiates script on topic: `{topic}`.")
    elif topic_user_wants_to_discuss:
        # user said `let's talk about [topic]` or
        # bot said `what do you want to talk about/would you like to switch the topic`,
        #   and user answered [topic] (not something, nothing, i don't know - in this case,
        #   it will be gone through previous if)
        topic = topic_user_wants_to_discuss
        response = TOPIC_SCRIPTS.get(topic, [""])[0]
        if topic in NOT_SCRIPTED_TOPICS:
            confidence = YES_CONTINUE_CONFIDENCE
        else:
            confidence = USER_TOPIC_START_CONFIDENCE
        logger.info(f"User initiates script on topic: `{topic}`.")
    else:
        topic = find_topics_in_substring(dialog["human_utterances"][-1]["text"])
        topic = topic[-1] if len(topic) else ""
        if len(topic) > 0:
            response = TOPIC_SCRIPTS.get(topic, [""])[0]
            confidence = FOUND_WORD_START_CONFIDENCE
            logger.info(f"Found word in user utterance on topic: `{topic}`.")
        else:
            topic = ""
            response = ""
            confidence = 0.0

    return response, topic, confidence


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
