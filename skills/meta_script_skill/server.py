#!/usr/bin/env python

import logging
import json
import time
from random import choice, uniform

from flask import Flask, request, jsonify
from os import getenv
import sentry_sdk

from common.constants import CAN_NOT_CONTINUE
from common.utils import get_skill_outputs_from_dialog
from utils import get_starting_phrase, get_statement_phrase, get_opinion_phrase, get_comment_phrase, \
    if_to_start_script


sentry_sdk.init(getenv('SENTRY_DSN'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

TOPICS = json.load(open("comet_predefined.json", "r"))
for _topic in TOPICS:
    for _relation in TOPICS[_topic]:
        TOPICS[_topic][_relation] = [el for el in TOPICS[_topic][_relation] if el != "none"]

DEFAULT_DIALOG_BEGIN_CONFIDENCE = 0.9
MATCHED_DIALOG_BEGIN_CONFIDENCE = 0.99


def get_not_used_topic(used_topics, dialog_begin=False):
    """
    Choose not used previously in the dialog topic.
    here choose one of the predefined topics

    Args:
        used_topics: topics already used in current dialog
        dialog_begin: if the dialog just began, and we can choose only predefined given topics. NOT YET AVAILABLE

    Returns:
        some topic `verb + adj/adv/noun` (like `go for shopping`, `practice yoga`, `play volleyball`)
    """
    all_topics = TOPICS.keys()
    available_topics = set(all_topics).difference(set(used_topics))
    if len(available_topics) > 0:
        return choice(list(available_topics))
    else:
        return ""


def get_status_and_topic(dialog):
    """
    Find prevously discussed meta-script topics, the last met-script status,
    determine current step meta-script status and topic.

    Args:
        dialog: dialog itself

    Returns:
        tuple of current status and topic
    """
    dialog_flow = ["starting", "deeper1", "deeper2", "deeper3", "opinion", "comment"]

    if len(dialog["utterances"]) >= 3:
        # if dialog is not empty
        meta_script_outputs = get_skill_outputs_from_dialog(dialog["utterances"],
                                                            skill_name="meta_script_skill", activated=True)
        used_topics = []
        for output in meta_script_outputs:
            used_topics.append(output.get("meta_script_topic", ""))
        logger.info(f"Previously used topics: {used_topics}")

        # this determines how many replies back we assume active meta script skill to continue dialog.
        # let's assume we can continue if meta_scrip skill was active on up to 3 steps back
        prev_reply_output = get_skill_outputs_from_dialog(dialog["utterances"][-7:],
                                                          skill_name="meta_script_skill", activated=True)
        if len(prev_reply_output) > 0:
            # previously active skill was `meta_script_skill`
            curr_meta_script_status = prev_reply_output[-1].get("meta_script_status", "")
        else:
            # previous active skill was not `meta_script_skill`
            curr_meta_script_status = ""
            curr_meta_script_topic = ""

        if curr_meta_script_status == "comment" or curr_meta_script_status == "":
            # if previous meta script is finished (comment given) in previous bot reply
            # or if no meta script in previous reply
            topic_switch_detected = dialog["utterances"][-1].get("annotations", {}).get(
                "intent_catcher", {}).get("topic_switching", {}).get("detected", 0) == 1
            if if_to_start_script(dialog) or topic_switch_detected:
                curr_meta_script_status = "starting"
                # choose new topic because in future we will take as topic smth from user's reply.
                curr_meta_script_topic = get_not_used_topic(used_topics)
            else:
                curr_meta_script_status = ""
                # choose new topic because in future we will take as topic smth from user's reply.
                curr_meta_script_topic = ""
        else:
            # some meta script is already in progress
            curr_meta_script_topic = used_topics[-1]
            logger.info(f"Found meta_script_status: `{curr_meta_script_status}` "
                        f"on previous meta_script_topic: `{curr_meta_script_topic}`")
            # getting the next dialog flow status
            curr_meta_script_status = dialog_flow[dialog_flow.index(curr_meta_script_status) + 1]
            if curr_meta_script_status == "deeper3":
                # randomly skip third deeper question
                if uniform(0, 1) <= 0.5:
                    curr_meta_script_status = "opinion"
        logger.info(f"New meta_script_status: `{curr_meta_script_status}` "
                    f"on meta_script_topic: `{curr_meta_script_topic}`")
    else:
        # start of the dialog, pick up a topic of meta script
        curr_meta_script_status = "starting"
        curr_meta_script_topic = get_not_used_topic([], dialog_begin=True)

    return curr_meta_script_status, curr_meta_script_topic


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
        human_attr = {}
        bot_attr = {}
        attr = {"can_continue": CAN_NOT_CONTINUE}

        curr_meta_script_status, topic = get_status_and_topic(dialog)
        topic_switch_detected = dialog["utterances"][-1].get("annotations", {}).get(
            "intent_catcher", {}).get("topic_switching", {}).get("detected", 0) == 1

        if topic != "":
            # if no available topic - skip with empty response!!!
            attr["meta_script_topic"] = topic
            attr["meta_script_status"] = curr_meta_script_status

            if curr_meta_script_status == "starting":
                response, confidence, attr = get_starting_phrase(topic, attr)
                if len(dialog["utterances"]) <= 10:
                    # if this is a beginning of the dialog, assign higher confidence to start the script
                    confidence = DEFAULT_DIALOG_BEGIN_CONFIDENCE
                if if_to_start_script(dialog) or topic_switch_detected:
                    confidence = MATCHED_DIALOG_BEGIN_CONFIDENCE
            else:
                # there were some script active before in the last several utterances
                if topic_switch_detected:
                    response, confidence, attr = "", 0.0, {}
                elif curr_meta_script_status == "comment":
                    response, confidence, attr = get_comment_phrase(dialog, attr)
                    # current meta script finished
                elif curr_meta_script_status == "opinion":
                    response, confidence, attr = get_opinion_phrase(topic, attr)
                else:
                    # do not consider three last used meta script templates
                    meta_script_outputs = get_skill_outputs_from_dialog(dialog["utterances"],
                                                                        skill_name="meta_script_skill", activated=True)
                    already_used_templates = []
                    for output in meta_script_outputs:
                        already_used_templates.append(output.get("meta_script_template_relation", ""))
                    logger.info(f"Found previously used relation templates:`{already_used_templates}`")
                    already_used_question_templates = []
                    for output in meta_script_outputs:
                        already_used_question_templates.append(output.get("meta_script_template_question", ""))
                    logger.info(f"Found previously used question templates:`{already_used_question_templates}`")

                    already_used_templates = [el for el in already_used_templates if el is not None][-4:]
                    already_used_question_templates = [el for el in already_used_question_templates
                                                       if el is not None][-4:]
                    response, confidence, attr = get_statement_phrase(
                        dialog, topic, attr, TOPICS, already_used_templates, already_used_question_templates)

            logger.info(f"User sent: `{dialog['utterances'][-1]['text']}`. "
                        f"Response: `{response}`."
                        f"Attr: `{attr}.`")
        else:
            # if no available topic
            response = ""
            confidence = 0.0

        responses.append(response)
        confidences.append(confidence)
        human_attributes.append(human_attr)
        bot_attributes.append(bot_attr)
        attributes.append(attr)

    total_time = time.time() - st_time
    logger.info(f'meta_script_skill exec time: {total_time:.3f}s')
    return jsonify(list(zip(responses, confidences, human_attributes, bot_attributes, attributes)))


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
