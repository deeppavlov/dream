#!/usr/bin/env python

import logging
import time
import re
from random import choice
import json

from flask import Flask, request, jsonify
from os import getenv
import sentry_sdk

from common.constants import CAN_NOT_CONTINUE, CAN_CONTINUE
from common.utils import get_skill_outputs_from_dialog


sentry_sdk.init(getenv('SENTRY_DSN'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


with open("topic_words.json", "r") as f:
    TOPIC_PATTERNS = json.load(f)

for topic in TOPIC_PATTERNS:
    words = TOPIC_PATTERNS[topic]
    pattern = "(" + "|".join(words) + ")"
    TOPIC_PATTERNS[topic] = re.compile(pattern)

with open("small_talk_scripts.json", "r") as f:
    TOPIC_SCRIPTS = json.load(f)

USER_TOPIC_START_CONFIDENCE = 0.99
FOUND_WORD_START_CONFIDENCE = 0.5
BOT_TOPIC_START_CONFIDENCE = 0.8
CONTINUE_CONFIDENCE = 0.99
LONG_ANSWER_CONTINUE_CONFIDENCE = 1.0
YES_CONTINUE_CONFIDENCE = 1.0


@app.route("/respond", methods=['POST'])
def respond():
    st_time = time.time()
    dialogs_batch = request.json["dialogs"]
    confidences = []
    responses = []
    human_attributes = []
    bot_attributes = []
    attributes = []

    for dialog in dialogs_batch:
        human_attr = dialog["human"]["attributes"]
        used_topics = human_attr.get("small_talk_topics", [])
        human_attr = {}
        bot_attr = {}
        attr = {}

        skill_outputs = get_skill_outputs_from_dialog(
            dialog["utterances"][-3:], skill_name="small_talk_skill", activated=True)
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

        _, new_user_topic, _ = pickup_topic_and_start_small_talk(dialog)
        logger.info(f"From current user utterance: `{dialog['human_utterances'][-1]['text']}` "
                    f"extracted topic: `{new_user_topic}`.")
        if len(topic) > 0 and len(new_user_topic) == 0 and len(script) > 0:
            response, confidence, attr = get_next_response_on_topic(
                topic, dialog["human_utterances"][-1], curr_step=script_step + 1, topic_script=script)
            if response != "":
                logger.info(f"Continue script on topic: `{topic}`.\n"
                            f"User utterance: `{dialog['human_utterances'][-1]['text']}`.\n"
                            f"Bot response: `{response}`.")
        else:
            logger.info("Try to extract topic from user utterance or offer if requested.")
            response, topic, confidence = pickup_topic_and_start_small_talk(dialog)
            if len(topic) > 0 and topic not in used_topics:
                logger.info(f"Starting script on topic: `{topic}`.\n"
                            f"User utterance: `{dialog['human_utterances'][-1]['text']}`.\n"
                            f"Bot response: `{response}`.")
                # topic script start, response is already formulated
                human_attr["small_talk_topics"] = used_topics + [topic]
                attr["can_continue"] = CAN_CONTINUE
                attr["small_talk_topic"] = topic
                attr["small_talk_step"] = 0
                attr["small_talk_script"] = TOPIC_SCRIPTS.get(topic, [])
            else:
                logger.info(f"Can not extract or offer topic.")

        if len(response) == 0:
            confidence = 0.

        responses.append(response)
        confidences.append(confidence)
        human_attributes.append(human_attr)
        bot_attributes.append(bot_attr)
        attributes.append(attr)

    total_time = time.time() - st_time
    logger.info(f'small_talk_skill exec time: {total_time:.3f}s')
    return jsonify(list(zip(responses, confidences, human_attributes, bot_attributes, attributes)))


def get_next_response_on_topic(topic, curr_user_uttr, curr_step=0, topic_script=[]):
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
        attr["can_continue"] = CAN_CONTINUE
        attr["small_talk_topic"] = topic
        attr["small_talk_step"] = curr_step
        if len(curr_user_uttr["text"].split()) > 7:
            confidence = LONG_ANSWER_CONTINUE_CONFIDENCE
        else:
            confidence = CONTINUE_CONFIDENCE
    elif isinstance(topic_script[curr_step], dict):
        yes_detected = curr_user_uttr["annotations"].get("intent_catcher", {}).get("yes", {}).get("detected", 0) == 1
        if yes_detected:
            next_bot_uttr = topic_script[curr_step]["yes"]
            attr["can_continue"] = CAN_CONTINUE
            attr["small_talk_topic"] = topic
            attr["small_talk_step"] = curr_step
            confidence = YES_CONTINUE_CONFIDENCE
        else:
            # consider all other answers as NO
            next_bot_uttr = topic_script[curr_step]["no"]
            attr["can_continue"] = CAN_CONTINUE
            attr["small_talk_topic"] = topic
            attr["small_talk_step"] = curr_step
            if len(curr_user_uttr["text"].split()) > 7:
                confidence = LONG_ANSWER_CONTINUE_CONFIDENCE
            else:
                confidence = CONTINUE_CONFIDENCE
    else:
        next_bot_uttr = ""
        confidence = 0.

    if isinstance(next_bot_uttr, list):
        attr["small_talk_script"] = topic_script[:curr_step] + next_bot_uttr + topic_script[curr_step + 1:]
        next_bot_uttr = attr["small_talk_script"][curr_step]
    else:
        attr["small_talk_script"] = topic_script[:curr_step] + [next_bot_uttr] + topic_script[curr_step + 1:]
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
    topic = choice(list(set(TOPIC_PATTERNS.keys()).difference(set(used_topics))))
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


def extract_topic_from_user_uttr(dialog):
    """
    Extract one of the considered topics out of `TOPIC_WORDS.keys()`.
    If none of them, return empty string.

    Args:
        dialog: dialog from agent

    Returns:
        string topic
    """
    talk_about = re.compile(r"about ([a-zA-Z\s0-9]+)")
    curr_user_uttr = dialog["human_utterances"][-1]["text"].lower()
    about_what = re.search(talk_about, curr_user_uttr)
    if about_what:
        # if user said "blabla about topic"
        topics = find_topics_in_substring(about_what.group(0))
    else:
        # if user said "sports" to questions "what do you wanna talk about"
        topics = find_topics_in_substring(curr_user_uttr)
    if len(topics) > 0:
        logger.info(f"Extracted topic `{topics[0]}` from user utterance.")
        return topics[0]
    else:
        return ""


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
        last_bot_uttr_text = dialog["bot_utterances"][-1]["text"].lower()
    else:
        last_bot_uttr_text = ""

    pickup_topic = re.compile(r"(pick up( the)? topic|give( me| us)?( a | the | some | )?topic)")
    what_to_talk_about = re.compile(r"what do you (want to|wanna) (talk|chat|have a conversation) about")
    switch_topic = re.compile(r"would you like to switch the topic")
    tell_me_about = re.compile(
        r"(tell me( something| anything)?( about)?|ask me( something| anything)?( about)?)")
    lets_talk_about = re.compile(
        r"(talk|chat|(have|hold|carry|turn on)( a | the | some | )?conversation|have( a | the | some | )?discussion"
        r"|converse|discuss|speak|say|talk)")
    not_detected = re.compile(r"(\bno\b|\bnot\b|n't)")
    # do you want to talk about something else
    lets_chat_about_detected = last_user_uttr.get("annotations", {}).get("intent_catcher", {}).get(
        "lets_chat_about", {}).get("detected", 0)
    topic_switching_detected = last_user_uttr.get("annotations", {}).get("intent_catcher", {}).get(
        "topic_switching", {}).get("detected", 0)

    if re.search(pickup_topic, last_user_uttr["text"].lower()) or re.search(
            what_to_talk_about, last_user_uttr["text"].lower()) or re.search(
            switch_topic, last_user_uttr["text"].lower()):
        # user said `what do you want to talk about/would you like to switch the topic`
        topic = offer_topic(dialog)
        if topic in TOPIC_PATTERNS:
            if topic == "me":
                response = f"Let's talk about you. " + TOPIC_SCRIPTS.get(topic, [""])[0]
            elif topic == "you":
                response = f"Let's talk about me. " + TOPIC_SCRIPTS.get(topic, [""])[0]
            else:
                response = f"Let's talk about {topic}. " + TOPIC_SCRIPTS.get(topic, [""])[0]
            confidence = BOT_TOPIC_START_CONFIDENCE
        else:
            response = ""
            confidence = 0.
        logger.info(f"Bot initiates script on topic: `{topic}`.")
    elif (lets_chat_about_detected or topic_switching_detected or re.search(
            pickup_topic, last_bot_uttr_text) or re.search(
            what_to_talk_about, last_bot_uttr_text) or re.search(
            switch_topic, last_bot_uttr_text) or re.search(
            tell_me_about, last_user_uttr["text"].lower()) or re.search(
            lets_talk_about, last_user_uttr["text"].lower())) and not re.search(
            not_detected, last_user_uttr["text"].lower()):
        # user said `let's talk about [something]` or
        # bot said `what do you want to talk about/would you like to switch the topic`, and user answered something
        topic = extract_topic_from_user_uttr(dialog)
        if len(topic) > 0:
            response = TOPIC_SCRIPTS.get(topic, [""])[0]
            confidence = USER_TOPIC_START_CONFIDENCE
            logger.info(f"User initiates script on topic: `{topic}`.")
        else:
            topic = offer_topic(dialog)
            if topic in TOPIC_PATTERNS:
                if topic == "me":
                    response = f"Let's talk about you. " + TOPIC_SCRIPTS.get(topic, [""])[0]
                elif topic == "you":
                    response = f"Let's talk about me. " + TOPIC_SCRIPTS.get(topic, [""])[0]
                else:
                    response = f"Let's talk about {topic}. " + TOPIC_SCRIPTS.get(topic, [""])[0]
                confidence = BOT_TOPIC_START_CONFIDENCE
                logger.info(f"Bot initiates script on topic: `{topic}`.")
            else:
                response = ""
                confidence = 0.
                logger.info(f"User initiates script but topic was not extracted.")

    else:
        topic = extract_topic_from_user_uttr(dialog)
        if len(topic) > 0:
            response = TOPIC_SCRIPTS.get(topic, [""])[0]
            confidence = FOUND_WORD_START_CONFIDENCE
            logger.info(f"Found word in user utterance on topic: `{topic}`.")
        else:
            topic = ""
            response = ""
            confidence = 0.

    return response, topic, confidence


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
