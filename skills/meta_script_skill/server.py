#!/usr/bin/env python

import logging
import json
import time
from random import choice, uniform, random

from flask import Flask, request, jsonify
from os import getenv
import sentry_sdk

from common.constants import CAN_NOT_CONTINUE
from common.utils import get_skill_outputs_from_dialog, get_user_replies_to_particular_skill
from common.universal_templates import if_choose_topic, if_switch_topic, if_lets_chat_about_topic
from utils import get_starting_phrase, get_statement_phrase, get_opinion_phrase, get_comment_phrase, \
    extract_verb_noun_phrases, DEFAULT_STARTING_CONFIDENCE, is_custom_topic, WIKI_DESCRIPTIONS, is_predefined_topic, \
    get_used_attributes_by_name
from comet_responses import ask_question_using_atomic, comment_using_atomic


sentry_sdk.init(getenv('SENTRY_DSN'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

TOPICS = json.load(open("comet_predefined.json", "r"))
for _topic in TOPICS:
    for _relation in TOPICS[_topic]:
        TOPICS[_topic][_relation] = [el for el in TOPICS[_topic][_relation] if el != "none"]

DEFAULT_DIALOG_BEGIN_CONFIDENCE = 0.8
MATCHED_DIALOG_BEGIN_CONFIDENCE = 0.99
FINISHED_SCRIPT_RESPONSE = "I see. Let's talk about something you want. Pick up the topic."
FINISHED_SCRIPT = "finished"


def get_not_used_topic(used_topics, dialog):
    """
    Choose not used previously in the dialog topic.
    here choose one of the predefined topics

    Args:
        used_topics: topics already used in current dialog

    Returns:
        some topic `verb + adj/adv/noun` (like `go for shopping`, `practice yoga`, `play volleyball`)
        and
        True is topic was extracted from user utterance and False otherwise
    """
    TOPICS_PROB = 0.3
    verb_noun_phrases = extract_verb_noun_phrases(dialog["utterances"][-1]["text"])

    if len(dialog['utterances']) < 3 or len(verb_noun_phrases) == 0:
        available_wiki_topics = set(WIKI_DESCRIPTIONS) - set(used_topics)
        available_topics = set(TOPICS) - set(used_topics)

        if random() < TOPICS_PROB and len(available_topics) > 0:
            return choice(list(available_topics)), False

        if len(available_wiki_topics) > 0:
            return choice(list(available_wiki_topics)), False

        return "", False
    else:
        return choice(verb_noun_phrases), True


def get_status_and_topic(dialog):
    """
    Find prevously discussed meta-script topics, the last met-script status,
    determine current step meta-script status and topic.

    Args:
        dialog: dialog itself

    Returns:
        tuple of current status and topic
    """
    # deeper2 and deeper3 could be randomly skipped in dialog flow
    dialog_flow = ["starting", "deeper1", "deeper2", "opinion", "comment"]
    dialog_flow_user_topic = ["deeper1", "deeper2", "opinion", "comment"]

    if len(dialog["utterances"]) >= 3:
        # if dialog is not empty

        used_topics = get_used_attributes_by_name(
            dialog["utterances"], attribute_name="meta_script_topic", value_by_default="", activated=True)

        # this determines how many replies back we assume active meta script skill to continue dialog.
        # let's assume we can continue if meta_scrip skill was active on up to 2 steps back
        prev_reply_output = get_skill_outputs_from_dialog(dialog["utterances"][-5:],
                                                          skill_name="meta_script_skill", activated=True)
        # get last meta script output even if it was not activated but right after it was active
        last_all_meta_script_outputs = get_skill_outputs_from_dialog(
            dialog["utterances"][-5:], skill_name="meta_script_skill", activated=False)
        prev_topic_finished = False
        for out in last_all_meta_script_outputs:
            if out.get("meta_script_status", "") == "finished":
                logger.info(f"Found finished dialog on meta_script_topic: `{out.get('meta_script_status', '')}`")
                prev_topic_finished = True

        if len(prev_reply_output) > 0:
            # previously active skill was `meta_script_skill`
            curr_meta_script_status = prev_reply_output[-1].get("meta_script_status", "")
        else:
            # previous active skill was not `meta_script_skill`
            curr_meta_script_status = ""
            curr_meta_script_topic = ""

        logger.info(f"Found meta_script_status: `{curr_meta_script_status}`")

        if curr_meta_script_status in ["comment", "", FINISHED_SCRIPT] or prev_topic_finished:
            # if previous meta script is finished (comment given) in previous bot reply
            # or if no meta script in previous reply or script was forcibly
            topic_switch_detected = dialog["utterances"][-1].get("annotations", {}).get(
                "intent_catcher", {}).get("topic_switching", {}).get("detected", 0) == 1
            topic, is_user_topic = get_not_used_topic(used_topics, dialog)

            if is_user_topic:
                curr_meta_script_status = dialog_flow_user_topic[0]
                curr_meta_script_topic = topic
            elif if_switch_topic(dialog["human_utterances"][-1]["text"].lower()) or \
                    if_choose_topic(dialog["human_utterances"][-1]["text"].lower(),
                                    prev_uttr=dialog["bot_utterances"][-1]["text"].lower()) or \
                    topic_switch_detected:
                curr_meta_script_status = dialog_flow[0]
                curr_meta_script_topic = topic
            else:
                curr_meta_script_status = ""
                curr_meta_script_topic = ""
        else:
            # some meta script is already in progress
            curr_meta_script_topic = used_topics[-1]
            logger.info(f"Found meta_script_status: `{curr_meta_script_status}` "
                        f"on previous meta_script_topic: `{curr_meta_script_topic}`")
            # getting the next dialog flow status
            if is_custom_topic(curr_meta_script_topic):
                curr_meta_script_status = dialog_flow_user_topic[dialog_flow_user_topic.index(
                    curr_meta_script_status) + 1]
            else:
                curr_meta_script_status = dialog_flow[dialog_flow.index(curr_meta_script_status) + 1]

            if curr_meta_script_status == "opinion":
                # randomly skip third deeper question
                if uniform(0, 1) <= 0.5:
                    curr_meta_script_status = "comment"
            if curr_meta_script_status == "deeper2":
                # randomly skip third deeper question
                if uniform(0, 1) <= 0.5:
                    curr_meta_script_status = "opinion"
        logger.info(f"New meta_script_status: `{curr_meta_script_status}` "
                    f"on meta_script_topic: `{curr_meta_script_topic}`")
    else:
        # start of the dialog, pick up a topic of meta script
        curr_meta_script_topic, _ = get_not_used_topic([], dialog)
        if is_custom_topic(curr_meta_script_topic):
            curr_meta_script_status = dialog_flow_user_topic[0]
        else:
            curr_meta_script_status = dialog_flow[0]

    return curr_meta_script_status, curr_meta_script_topic


@app.route("/respond", methods=['POST'])
def respond():
    st_time = time.time()
    dialogs_batch = request.json["dialogs"]
    final_responses = []
    final_confidences = []
    final_attributes = []

    for dialog in dialogs_batch:
        curr_responses = []
        curr_confidences = []
        curr_attrs = []

        attr = {"can_continue": CAN_NOT_CONTINUE}

        curr_meta_script_status, topic = get_status_and_topic(dialog)
        topic_switch_detected = dialog["utterances"][-1].get("annotations", {}).get(
            "intent_catcher", {}).get("topic_switching", {}).get("detected", 0) == 1

        lets_chat_about_detected = dialog["utterances"][-1].get("annotations", {}).get(
            "intent_catcher", {}).get("lets_chat_about", {}).get("detected", 0) == 1

        yes_detected = dialog["utterances"][-1].get("annotations", {}).get(
            "intent_catcher", {}).get("yes", {}).get("detected", 0) == 1
        no_detected = dialog["utterances"][-1].get("annotations", {}).get(
            "intent_catcher", {}).get("no", {}).get("detected", 0) == 1
        never_detected = "never" in dialog["utterances"][-1]["text"].lower()

        last_two_user_responses = get_user_replies_to_particular_skill(dialog["utterances"], "meta_script_skill")[-2:]

        if topic != "":
            # if no available topic - skip with empty response!!!
            attr["meta_script_topic"] = topic
            attr["meta_script_status"] = curr_meta_script_status

            if curr_meta_script_status == "starting":
                response, confidence, attr = get_starting_phrase(dialog, topic, attr)
                if (len(dialog["bot_utterances"]) > 0 and if_choose_topic(
                        dialog["human_utterances"][-1]["text"].lower(),
                        prev_uttr=dialog["bot_utterances"][-1]["text"].lower())) or \
                        (len(dialog["bot_utterances"]) == 0 and if_choose_topic(
                            dialog["human_utterances"][-1]["text"].lower())) or \
                        if_switch_topic(dialog["human_utterances"][-1]["text"].lower()) or \
                        topic_switch_detected:
                    confidence = MATCHED_DIALOG_BEGIN_CONFIDENCE
                elif len(dialog["human_utterances"]) > 0 and \
                        if_lets_chat_about_topic(dialog["human_utterances"][-1]["text"].lower()):
                    # if person wants to talk about something particular - do not start script!
                    response, confidence = "", 0.
                elif len(dialog["human_utterances"]) > 0 and "?" in dialog["human_utterances"][-1]["text"]:
                    # if some question was asked by user, do not start script at all!
                    response, confidence = "", 0.
                elif len(dialog["utterances"]) <= 20:
                    # if this is a beginning of the dialog, assign higher confidence to start the script
                    confidence = DEFAULT_DIALOG_BEGIN_CONFIDENCE
                else:
                    confidence = DEFAULT_STARTING_CONFIDENCE
            else:
                # there were some script active before in the last several utterances
                if len(dialog["human_utterances"]) > 0 and "?" in dialog["human_utterances"][-1]["text"]:
                    logger.info("Question by user was detected. Don't continue the script on this turn.")
                    response, confidence, attr = "", 0., {}
                    # we do not finish script on this step but hope that some other script will be able
                    # to answer user's question
                elif topic_switch_detected or lets_chat_about_detected:
                    logger.info("Topic switching was detected. Finish script.")
                    response, confidence = FINISHED_SCRIPT_RESPONSE, 0.5
                    attr["meta_script_status"] = FINISHED_SCRIPT
                elif last_two_user_responses == ["no.", "no."]:
                    logger.info("Two consequent `no` answers were detected. Finish script.")
                    response, confidence = FINISHED_SCRIPT_RESPONSE, 0.5
                    attr["meta_script_status"] = FINISHED_SCRIPT
                elif curr_meta_script_status == "comment":
                    response, confidence, attr = get_comment_phrase(dialog, attr)
                    # current meta script finished
                elif curr_meta_script_status == "opinion":
                    response, confidence, attr = get_opinion_phrase(dialog, topic, attr)
                elif curr_meta_script_status == "deeper1" and (
                        no_detected or never_detected) and not is_predefined_topic(topic):
                    # some `no`-intended answer to starting phrase from wiki or custom topic (not for predefined)
                    response, confidence = FINISHED_SCRIPT_RESPONSE, 0.5
                    attr["meta_script_status"] = FINISHED_SCRIPT
                else:
                    response, confidence, attr = get_statement_phrase(dialog, topic, attr, TOPICS)

            if confidence > 0.7 and (yes_detected or len(dialog["utterances"][-1]["text"].split()) > 7):
                # if yes detected, confidence 1.0 - we like agreements!
                confidence = 1.0

            logger.info(f"User sent: `{dialog['utterances'][-1]['text']}`. "
                        f"Response: `{response}`."
                        f"Attr: `{attr}.`")
        else:
            # if no available topic
            response, confidence, attr = "", 0., {}

        curr_responses.append(response)
        curr_confidences.append(confidence)
        curr_attrs.append(attr)

        comet_dialog_status = get_used_attributes_by_name(
            dialog["utterances"][-3:], attribute_name="atomic_dialog",
            value_by_default=None, activated=True)
        if len(comet_dialog_status) > 0 and comet_dialog_status[-1] == "ask_question":
            logger.info(f"Found previous comet dialog status: {comet_dialog_status}")
            response, confidence, attr = comment_using_atomic(dialog)
        else:
            response, confidence, attr = ask_question_using_atomic(dialog)
        curr_responses.append(response)
        curr_confidences.append(confidence)
        curr_attrs.append(attr)

        final_responses.append(curr_responses)
        final_confidences.append(curr_confidences)
        final_attributes.append(curr_attrs)

    total_time = time.time() - st_time
    logger.info(f'meta_script_skill exec time: {total_time:.3f}s')
    return jsonify(list(zip(final_responses, final_confidences, final_attributes)))


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
