#!/usr/bin/env python

import logging
import json
from random import choice, uniform, random
import pathlib

from os import getenv
import sentry_sdk

from common.constants import CAN_CONTINUE_SCENARIO, CAN_NOT_CONTINUE
from common.utils import (
    get_skill_outputs_from_dialog,
    get_user_replies_to_particular_skill,
    is_no,
    is_yes,
    get_outputs_with_response_from_dialog,
    get_entities,
)
from common.universal_templates import if_choose_topic, if_chat_about_particular_topic, is_switch_topic
from common.news import OPINION_REQUEST_STATUS, OFFERED_NEWS_DETAILS_STATUS
from common.greeting import GREETING_QUESTIONS
from utils import (
    get_starting_phrase,
    get_statement_phrase,
    get_opinion_phrase,
    get_comment_phrase,
    extract_verb_noun_phrases,
    is_custom_topic,
    WIKI_DESCRIPTIONS,
    get_used_attributes_by_name,
    check_topic_lemmas_in_sentence,
)
from constants import (
    DEFAULT_DIALOG_BEGIN_CONFIDENCE,
    MATCHED_DIALOG_BEGIN_CONFIDENCE,
    FINISHED_SCRIPT,
    FINISHED_SCRIPT_RESPONSE,
    DEFAULT_STARTING_CONFIDENCE,
    NOUN_TOPIC_STARTING_CONFIDENCE,
    NP_SOURCE,
    PREDEFINED_SOURCE,
    BROKEN_DIALOG_CONTINUE_CONFIDENCE,
    NUMBER_OF_STARTING_HYPOTHESES_META_SCRIPT,
)


sentry_sdk.init(getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

WORK_DIR = pathlib.Path(__file__).parent

TOPICS = json.load((WORK_DIR / "comet_predefined.json").open())

for _topic in TOPICS:
    for _relation in TOPICS[_topic]:
        TOPICS[_topic][_relation] = [el for el in TOPICS[_topic][_relation] if el != "none"]


def extract_from_dialog(dialog):
    prev_news_outputs = get_skill_outputs_from_dialog(dialog["utterances"][-3:], "news_api_skill", activated=True)
    if len(prev_news_outputs) > 0:
        prev_news_output = prev_news_outputs[-1]
    else:
        prev_news_output = {}
    no_detected = is_no(dialog["human_utterances"][-1])
    nounphrases = get_entities(dialog["human_utterances"][-1], only_named=False, with_labels=False)

    if prev_news_output.get("news_status", "finished") == OPINION_REQUEST_STATUS or (
        prev_news_output.get("news_status", "finished") == OFFERED_NEWS_DETAILS_STATUS and no_detected
    ):
        verb_noun_phrases, sources = extract_verb_noun_phrases(
            prev_news_outputs[-1].get("text", "nothing"), only_i_do_that=False, nounphrases=nounphrases
        )
    else:
        verb_noun_phrases, sources = extract_verb_noun_phrases(
            dialog["utterances"][-1]["text"], only_i_do_that=False, nounphrases=nounphrases
        )
    return verb_noun_phrases, sources


def get_not_used_topics(used_topics, dialog):
    """
    Choose not used previously in the dialog topic.
    here choose one of the predefined topics

    Args:
        used_topics: topics already used in current dialog

    Returns:
        some topic `verb + adj/adv/noun` (like `go for shopping`, `practice yoga`, `play volleyball`)
        and
        2, if noun was extracted from user utterance, and found verb for bigram,
        1, if verb+noun topic was extracted from user utterance,
        0, otherwise
    """
    TOPICS_PROB = 0.3
    verb_noun_phrases, sources = extract_from_dialog(dialog)

    if len(verb_noun_phrases) == 0:
        available_wiki_topics = set(WIKI_DESCRIPTIONS) - set(used_topics)
        available_topics = set(TOPICS) - set(used_topics)

        if (random() < TOPICS_PROB or len(dialog["utterances"]) == 1) and len(available_topics) > 0:
            return [choice(list(available_topics))], [PREDEFINED_SOURCE]

        if len(available_wiki_topics) > 0:
            return [choice(list(available_wiki_topics))], [PREDEFINED_SOURCE]

        return [""], [PREDEFINED_SOURCE]
    else:
        return verb_noun_phrases, sources


def get_statuses_and_topics(dialog):
    """
    Find prevously discussed meta-script topics, the last met-script status,
    determine current step meta-script status and topic.

    Args:
        dialog: dialog itself

    Returns:
        tuple of current status and topic
    """
    # deeper2 and opinion could be randomly skipped in dialog flow
    dialog_flow = ["starting", "deeper1", "deeper2", "opinion", "comment"]
    dialog_flow_user_topic = ["starting", "deeper1", "comment"]
    curr_meta_script_statuses = []
    curr_meta_script_topics = []
    source_topics = []

    if len(dialog["utterances"]) >= 3:
        # if dialog is not empty

        used_topics = get_used_attributes_by_name(
            dialog["utterances"], attribute_name="meta_script_topic", value_by_default="", activated=True
        )

        # this determines how many replies back we assume active meta script skill to continue dialog.
        # let's assume we can continue if meta_scrip skill was active on up to 2 steps back
        prev_reply_output = get_skill_outputs_from_dialog(
            dialog["utterances"][-5:], skill_name="meta_script_skill", activated=True
        )
        # get last meta script output even if it was not activated but right after it was active
        last_all_meta_script_outputs = get_skill_outputs_from_dialog(
            dialog["utterances"][-5:], skill_name="meta_script_skill", activated=False
        )
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
        logger.info(f"Found meta_script_status: `{curr_meta_script_status}`")

        if curr_meta_script_status in ["comment", "", FINISHED_SCRIPT] or prev_topic_finished:
            # if previous meta script is finished (comment given) in previous bot reply
            # or if no meta script in previous reply or script was forcibly
            topics, curr_source_topics = get_not_used_topics(used_topics, dialog)
            if curr_source_topics != [PREDEFINED_SOURCE]:
                # if topic is extracted from utterances
                pass
            elif if_choose_topic(dialog["human_utterances"][-1], dialog["bot_utterances"][-1]):
                # len(utterances) >3 so at least 1 bot utterance exists
                # one of the predefined topics (wiki or hand-written)
                curr_meta_script_statuses += [dialog_flow[0]] * len(topics)
                curr_meta_script_topics += topics
                source_topics += curr_source_topics
            else:
                pass
        else:
            # some meta script is already in progress
            # we define it here as predefined because we do not care about this variable if it's not script starting
            source_topic = PREDEFINED_SOURCE
            curr_meta_script_topic = used_topics[-1]
            logger.info(
                f"Found meta_script_status: `{curr_meta_script_status}` "
                f"on previous meta_script_topic: `{curr_meta_script_topic}`"
            )
            # getting the next dialog flow status
            if is_custom_topic(curr_meta_script_topic):
                curr_meta_script_status = dialog_flow_user_topic[
                    dialog_flow_user_topic.index(curr_meta_script_status) + 1
                ]
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
            logger.info(
                f"New meta_script_status: `{curr_meta_script_status}` "
                f"on meta_script_topic: `{curr_meta_script_topic}`"
            )
            curr_meta_script_statuses += [curr_meta_script_status]
            curr_meta_script_topics += [curr_meta_script_topic]
            source_topics += [source_topic]
    else:
        # start of the dialog, pick up a topic of meta script
        curr_meta_script_topics, source_topics = get_not_used_topics([], dialog)
        if source_topics != [PREDEFINED_SOURCE]:
            curr_meta_script_statuses = [dialog_flow_user_topic[0]] * len(curr_meta_script_topics)
        else:
            curr_meta_script_statuses = [dialog_flow[0]] * len(curr_meta_script_topics)

    logger.info(
        f"Final new meta_script_status: `{curr_meta_script_statuses}` "
        f"on meta_script_topic: `{curr_meta_script_topics}`"
    )
    return curr_meta_script_statuses, curr_meta_script_topics, source_topics


def get_response_for_particular_topic_and_status(topic, curr_meta_script_status, dialog, source_topic):
    attr = {"meta_script_topic": topic, "meta_script_status": curr_meta_script_status}

    if len(dialog["human_utterances"]) > 0:
        user_uttr = dialog["human_utterances"][-1]
        text_user_uttr = dialog["human_utterances"][-1]["text"].lower()
        last_user_sent_text = (
            dialog["human_utterances"][-1].get("annotations", {}).get("sentseg", {}).get("segments", [""])[-1].lower()
        )
    else:
        user_uttr = {"text": ""}
        text_user_uttr = ""
        last_user_sent_text = ""
    if len(dialog["bot_utterances"]) > 0:
        bot_uttr = dialog["bot_utterances"][-1]
    else:
        bot_uttr = {}
    if curr_meta_script_status == "starting":
        response, confidence, attr = get_starting_phrase(dialog, topic, attr)
        attr["response_parts"] = ["prompt"]
        can_offer_topic = if_choose_topic(dialog["human_utterances"][-1], bot_uttr)
        talk_about_user_topic = is_custom_topic(topic) and if_chat_about_particular_topic(user_uttr, bot_uttr)

        prev_what_to_talk_about_outputs = [
            get_outputs_with_response_from_dialog(dialog["utterances"][-3:], response=response, activated=True)
            for response in GREETING_QUESTIONS[list(GREETING_QUESTIONS.keys())[0]]
        ]
        prev_what_to_talk_about_outputs = sum(
            [list_of_outputs for list_of_outputs in prev_what_to_talk_about_outputs if len(list_of_outputs) > 0], []
        )
        prev_what_to_talk_about_greeting = len(prev_what_to_talk_about_outputs) > 0 and bot_uttr.get(
            "active_skill", ""
        ) in ["dff_friendship_skill", "program_y"]

        if (not prev_what_to_talk_about_greeting and can_offer_topic) or talk_about_user_topic:
            # if person wants to talk about something particular and we have extracted some topic - do that!
            confidence = MATCHED_DIALOG_BEGIN_CONFIDENCE
        elif "?" in last_user_sent_text or prev_what_to_talk_about_greeting:
            # if some question was asked by user, do not start script at all!
            response, confidence = "", 0.0
        elif len(dialog["utterances"]) <= 20:
            confidence = DEFAULT_DIALOG_BEGIN_CONFIDENCE
        elif source_topic == NP_SOURCE:
            confidence = NOUN_TOPIC_STARTING_CONFIDENCE
        else:
            confidence = DEFAULT_STARTING_CONFIDENCE
    else:
        if curr_meta_script_status == "deeper1" and "?" in last_user_sent_text and "what" not in text_user_uttr:
            response, confidence, attr = "", 0.0, {}
        elif "?" in last_user_sent_text and not check_topic_lemmas_in_sentence(text_user_uttr, topic):
            logger.info(
                "Question by user was detected. Without any word from topic in it. "
                "Don't continue the script on this turn."
            )
            response, confidence, attr = "", 0.0, {}
        elif is_switch_topic(user_uttr) or if_chat_about_particular_topic(user_uttr):
            logger.info("Topic switching was detected. Finish script.")
            response, confidence = FINISHED_SCRIPT_RESPONSE, 0.5
            attr["meta_script_status"] = FINISHED_SCRIPT
            attr["can_continue"] = CAN_NOT_CONTINUE
        elif get_user_replies_to_particular_skill(dialog["utterances"], "meta_script_skill")[-2:] == ["no.", "no."]:
            logger.info("Two consequent `no` answers were detected. Finish script.")
            response, confidence = FINISHED_SCRIPT_RESPONSE, 0.5
            attr["meta_script_status"] = FINISHED_SCRIPT
            attr["can_continue"] = CAN_NOT_CONTINUE
        elif curr_meta_script_status == "comment":
            response, confidence, attr = get_comment_phrase(dialog, attr)
            attr["can_continue"] = CAN_NOT_CONTINUE
        elif curr_meta_script_status == "opinion":
            response, confidence, attr = get_opinion_phrase(dialog, topic, attr)
        elif curr_meta_script_status == "deeper1" and (is_no(user_uttr) or "never" in text_user_uttr):
            response, confidence = FINISHED_SCRIPT_RESPONSE, 0.5
            attr["meta_script_status"] = FINISHED_SCRIPT
            attr["can_continue"] = CAN_NOT_CONTINUE
        else:
            response, confidence, attr = get_statement_phrase(dialog, topic, attr, TOPICS)
            attr["can_continue"] = CAN_CONTINUE_SCENARIO

        if confidence > 0.7 and (is_yes(user_uttr) or len(text_user_uttr.split()) > 7):
            # if yes detected, confidence 1.0 - we like agreements!
            confidence = 1.0
        if confidence > 0.7 and bot_uttr.get("active_skill", "") != "meta_script_skill":
            confidence = BROKEN_DIALOG_CONTINUE_CONFIDENCE

    logger.info(f"User sent: `{text_user_uttr}`. Response: `{response}`. Attr: `{attr}.`")
    return response, confidence, attr


def respond_meta_script(dialogs_batch):
    final_responses = []
    final_confidences = []
    final_attributes = []

    for dialog in dialogs_batch:
        curr_responses = []
        curr_confidences = []
        curr_attrs = []

        curr_meta_script_statuses, curr_meta_script_topics, source_topics = get_statuses_and_topics(dialog)
        for status, topic, source in zip(
            curr_meta_script_statuses[:NUMBER_OF_STARTING_HYPOTHESES_META_SCRIPT],
            curr_meta_script_topics[:NUMBER_OF_STARTING_HYPOTHESES_META_SCRIPT],
            source_topics[:NUMBER_OF_STARTING_HYPOTHESES_META_SCRIPT],
        ):
            if topic != "":
                response, confidence, attr = get_response_for_particular_topic_and_status(topic, status, dialog, source)
                curr_responses.append(response)
                curr_confidences.append(confidence)
                curr_attrs.append(attr)

        if len(curr_responses) == 0:
            response, confidence, attr = "", 0.0, {}
            curr_responses.append(response)
            curr_confidences.append(confidence)
            curr_attrs.append(attr)

        final_responses.append(curr_responses)
        final_confidences.append(curr_confidences)
        final_attributes.append(curr_attrs)

    return final_responses, final_confidences, final_attributes
