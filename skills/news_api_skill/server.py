#!/usr/bin/env python

import logging
import os
import re
import random
import string
from collections import defaultdict
from os import getenv
from time import time

import numpy as np
import sentry_sdk
from flask import Flask, request, jsonify
from nltk.tokenize import word_tokenize

from common.constants import CAN_CONTINUE_PROMPT, MUST_CONTINUE
from common.link import link_to, SKILLS_TO_BE_LINKED_EXCEPT_LOW_RATED
from common.metrics import setup_metrics
from common.news import (
    OFFER_BREAKING_NEWS,
    OFFERED_BREAKING_NEWS_STATUS,
    OFFERED_NEWS_DETAILS_STATUS,
    OPINION_REQUEST_STATUS,
    WHAT_TYPE_OF_NEWS,
    SAY_TOPIC_SPECIFIC_NEWS,
    OFFER_TOPIC_SPECIFIC_NEWS_STATUS,
    OFFERED_NEWS_TOPIC_CATEGORIES_STATUS,
    was_offer_news_about_topic,
    get_news_about_topic,
    extract_topics,
    EXTRACT_OFFERED_NEWS_TOPIC_TEMPLATE,
)
from common.utils import get_skill_outputs_from_dialog, is_yes, is_no, get_topics
from common.universal_templates import (
    COMPILE_NOT_WANT_TO_TALK_ABOUT_IT,
    COMPILE_SWITCH_TOPIC,
    if_chat_about_particular_topic,
)


sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
setup_metrics(app)

N_FACTS_TO_CHOSE = 3

NEWS_API_ANNOTATOR_URL = os.environ.get("NEWS_API_ANNOTATOR_URL")

NEWS_TOPICS = ["Sports", "Politics", "Economy", "Science", "Arts", "Health", "Education"]

DEFAULT_NEWS_OFFER_CONFIDENCE = 1.0
WHAT_TYPE_OF_NEWS_CONFIDENCE = 0.9
NOT_SPECIFIC_NEWS_OFFER_CONFIDENCE = 1.0
DEFAULT_NEWS_DETAILS_CONFIDENCE = 1.0
LINKTO_CONFIDENCE = 0.9
LINKTO_FOR_LONG_RESPONSE_CONFIDENCE = 0.7
OFFER_MORE = "Do you want to hear more?"
ASK_OPINION = "What do you think about it?"

NEWS_TEMPLATES = re.compile(r"(tell (me )?(some )?news|(what is|what's)( the)? new|something new)", re.IGNORECASE)
FALSE_NEWS_TEMPLATES = re.compile(r"(s good news|s bad news|s sad news|s awful news|s terrible news)", re.IGNORECASE)
TELL_MORE_NEWS_TEMPLATES = re.compile(
    r"(tell me more|tell me next|more news|next news|other news|learn more)", re.IGNORECASE
)
ANY_TOPIC_PATTERN = re.compile(r"\b(first|any|both|either|all|don't know|not know)\b", re.IGNORECASE)
SECOND_TOPIC_PATTERN = re.compile(r"\b(second|last)\b", re.IGNORECASE)


def remove_punct_and_articles(s, lowecase=True):
    articles = ["a", "the"]
    if lowecase:
        s = s.lower()
    no_punct = "".join([c for c in s if c not in string.punctuation])
    no_articles = " ".join([w for w in word_tokenize(no_punct) if w.lower() not in articles])
    return no_articles


def news_rejection(uttr):
    if re.search(COMPILE_NOT_WANT_TO_TALK_ABOUT_IT, uttr):
        return True
    elif re.search(COMPILE_SWITCH_TOPIC, uttr):
        return True
    elif "nothing" in uttr or "none" in uttr:
        return True
    else:
        return False


def get_news_for_current_entity(entity, curr_uttr, discussed_news):
    curr_news_api_annotation = curr_uttr.get("annotations", {}).get("news_api", [])
    for news_el in curr_news_api_annotation:
        if news_el["entity"] == entity:
            return news_el["news"]

    result = get_news_about_topic(entity, NEWS_API_ANNOTATOR_URL, discussed_news=discussed_news, timeout_value=1.5)
    if result:
        return result

    return {}


def collect_topics_and_statuses(dialogs):
    topics = []
    statuses = []
    curr_news_samples = []
    for dialog in dialogs:
        curr_uttr = dialog["human_utterances"][-1]
        prev_uttr = dialog["bot_utterances"][-1] if len(dialog["bot_utterances"]) else {}
        human_attr = {}
        human_attr["news_api_skill"] = dialog["human"]["attributes"].get("news_api_skill", {})
        discussed_news = human_attr["news_api_skill"].get("discussed_news", [])
        prev_bot_uttr = dialog["bot_utterances"][-1] if len(dialog["bot_utterances"]) > 0 else {}
        prev_bot_uttr_lower = prev_bot_uttr.get("text", "").lower()

        prev_news_skill_output = get_skill_outputs_from_dialog(
            dialog["utterances"][-3:], skill_name="news_api_skill", activated=True
        )

        if len(prev_news_skill_output) > 0 and len(prev_news_skill_output[-1]) > 0:
            logger.info("News skill was prev active.")
            prev_news_skill_output = prev_news_skill_output[-1]
            prev_status = prev_news_skill_output.get("news_status", "")
            prev_topic = prev_news_skill_output.get("news_topic", "all")
            last_news = prev_news_skill_output.get("curr_news", {})
            if prev_status == OFFERED_NEWS_DETAILS_STATUS:
                topics.append(prev_topic)
                if is_yes(curr_uttr):
                    logger.info(f"Detected topic for news: {prev_topic}")
                    statuses.append("details")
                else:
                    logger.info("User refused to get news details")
                    statuses.append("finished")
                curr_news_samples.append(last_news)
            elif prev_status == OFFERED_BREAKING_NEWS_STATUS or OFFER_BREAKING_NEWS.lower() in prev_bot_uttr_lower:
                topics.append("all")
                if is_yes(curr_uttr):
                    logger.info("Detected topic for news: all.")
                    statuses.append("headline")
                else:
                    logger.info("User refuse to get latest news")
                    statuses.append("declined")
                curr_news_samples.append(last_news)
            elif re.search(TELL_MORE_NEWS_TEMPLATES, curr_uttr["text"].lower()):
                prev_news_skill_output = get_skill_outputs_from_dialog(
                    dialog["utterances"][-7:], skill_name="news_api_skill", activated=True
                )
                for prev_news_out in prev_news_skill_output:
                    if prev_news_out.get("curr_news", {}) != {}:
                        last_news = prev_news_out.get("curr_news", {})
                logger.info(f"User requested more news. Prev news was: {last_news}")
                topics.append(prev_topic)
                statuses.append("headline")
                curr_news_samples.append(get_news_for_current_entity(prev_topic, curr_uttr, discussed_news))
            elif prev_status == OFFERED_NEWS_TOPIC_CATEGORIES_STATUS:
                if not (news_rejection(curr_uttr["text"].lower()) or is_no(curr_uttr)):
                    logger.info("User chose the topic for news")
                    if ANY_TOPIC_PATTERN.search(curr_uttr["text"]):
                        topics.append(prev_topic.split()[0])
                        curr_news_samples.append(
                            get_news_for_current_entity(prev_topic.split()[0], curr_uttr, discussed_news)
                        )
                    elif SECOND_TOPIC_PATTERN.search(curr_uttr["text"]):
                        topics.append(prev_topic.split()[1])
                        curr_news_samples.append(
                            get_news_for_current_entity(prev_topic.split()[1], curr_uttr, discussed_news)
                        )
                    else:
                        entities = extract_topics(curr_uttr)
                        if len(entities) != 0:
                            topics.append(entities[-1])
                            curr_news_samples.append(
                                get_news_for_current_entity(entities[-1], curr_uttr, discussed_news)
                            )
                        else:
                            topics.append("all")
                            curr_news_samples.append(get_news_for_current_entity("all", curr_uttr, discussed_news))
                    logger.info(f"Chosen topic: {topics}")
                    statuses.append("headline")
                else:
                    logger.info("User doesn't want to get any news")
                    topics.append("all")
                    statuses.append("declined")
                    curr_news_samples.append({})
            elif prev_status == OFFER_TOPIC_SPECIFIC_NEWS_STATUS:
                topics.append(prev_topic)
                if is_yes(curr_uttr):
                    logger.info(f"User wants to listen news about {prev_topic}.")
                    statuses.append("headline")
                else:
                    logger.info(f"User doesn't want to listen news about {prev_topic}.")
                    statuses.append("declined")
                curr_news_samples.append(last_news)
            else:
                logger.info("News skill was active and now can offer more news.")
                topics.append("all")
                statuses.append("finished")
                curr_news_samples.append(get_news_for_current_entity("all", curr_uttr, discussed_news))
        else:
            logger.info("News skill was NOT active.")
            about_news = (
                ({"News"} & set(get_topics(curr_uttr, which="cobot_topics")))
                or re.search(NEWS_TEMPLATES, curr_uttr["text"].lower())
            ) and not re.search(FALSE_NEWS_TEMPLATES, curr_uttr["text"].lower())
            lets_chat_about_particular_topic = if_chat_about_particular_topic(curr_uttr, prev_uttr)
            lets_chat_about_news = if_chat_about_particular_topic(curr_uttr, prev_uttr, compiled_pattern=NEWS_TEMPLATES)
            _was_offer_news = was_offer_news_about_topic(prev_bot_uttr_lower)
            _offered_by_bot_entities = EXTRACT_OFFERED_NEWS_TOPIC_TEMPLATE.findall(prev_bot_uttr_lower)

            if about_news:
                # the request contains something about news
                entities = extract_topics(curr_uttr)
                logger.info(f"News request on entities: `{entities}`")
                if re.search(TELL_MORE_NEWS_TEMPLATES, curr_uttr["text"].lower()):
                    # user requestd more news.
                    # look for the last 3 turns and find last discussed news sample
                    logger.info("Tell me more news request.")
                    prev_news_skill_output = get_skill_outputs_from_dialog(
                        dialog["utterances"][-7:], skill_name="news_api_skill", activated=True
                    )
                    if len(prev_news_skill_output) > 0 and len(prev_news_skill_output[-1]) > 0:
                        prev_news_skill_output = prev_news_skill_output[-1]
                        prev_topic = prev_news_skill_output.get("news_topic", "all")
                    else:
                        prev_topic = "all"
                    logger.info("News skill was NOT prev active. User requested more news.")
                    topics.append(prev_topic)
                    statuses.append("headline")
                    curr_news_samples.append(get_news_for_current_entity(prev_topic, curr_uttr, discussed_news))
                elif len(entities) == 0:
                    # no entities or nounphrases -> no special news request, get all news
                    logger.info("News request, no entities and nounphrases.")
                    topics.append("all")
                    statuses.append("headline")
                    curr_news_samples.append(get_news_for_current_entity("all", curr_uttr, discussed_news))
                else:
                    # found entities or nounphrases -> special news request,
                    # get the last mentioned entity
                    # if no named entities, get the last mentioned nounphrase
                    logger.info(f"Detected topic for news: {entities[-1]}")
                    topics.append(entities[-1])
                    statuses.append("headline")
                    curr_news_samples.append(get_news_for_current_entity(entities[-1], curr_uttr, discussed_news))
            elif OFFER_BREAKING_NEWS.lower() in prev_bot_uttr_lower:
                # news skill was not previously active
                topics.append("all")
                if is_yes(curr_uttr) or lets_chat_about_news:
                    logger.info("Detected topic for news: all.")
                    statuses.append("headline")
                else:
                    logger.info("Detected topic for news: all. Refused to get latest news")
                    statuses.append("declined")
                curr_news_samples.append(get_news_for_current_entity("all", curr_uttr, discussed_news))
            elif _was_offer_news and _offered_by_bot_entities:
                topics.append(_offered_by_bot_entities[-1])
                if is_yes(curr_uttr):
                    logger.info(f"Bot offered news on entities: `{_offered_by_bot_entities}`")
                    statuses.append("headline")
                else:
                    logger.info(f"Bot offered news on entities: `{_offered_by_bot_entities}`. User refused.")
                    statuses.append("declined")
                curr_news_samples.append(
                    get_news_for_current_entity(_offered_by_bot_entities[-1], curr_uttr, discussed_news)
                )
            elif lets_chat_about_particular_topic:
                # the request contains something about news
                entities = extract_topics(curr_uttr)
                logger.info(f"News request on entities: `{entities}`")
                if len(entities) == 0:
                    # no entities or nounphrases & lets_chat_about_particular_topic
                    logger.info("No news request, no entities and nounphrases, but lets chat.")
                    topics.append("all")
                    statuses.append("declined")
                    curr_news_samples.append({})
                else:
                    # found entities or nounphrases -> special news request,
                    # get the last mentioned entity
                    # if no named entities, get the last mentioned nounphrase
                    logger.info(f"Detected topic for news: {entities[-1]}")
                    topics.append(entities[-1])
                    statuses.append("headline")
                    curr_news_samples.append(get_news_for_current_entity(entities[-1], curr_uttr, discussed_news))
            else:
                logger.info("Didn't detected news request.")
                topics.append("all")
                statuses.append("declined")
                curr_news_samples.append({})
    return topics, statuses, curr_news_samples


def link_to_other_skills(human_attr, bot_attr, curr_uttr):
    link = link_to(
        SKILLS_TO_BE_LINKED_EXCEPT_LOW_RATED, human_attributes=human_attr, recent_active_skills=["news_api_skill"]
    )
    response = link["phrase"]
    if len(curr_uttr["text"].split()) <= 5 and not re.search(FALSE_NEWS_TEMPLATES, curr_uttr["text"]):
        confidence = LINKTO_CONFIDENCE
    elif re.search(FALSE_NEWS_TEMPLATES, curr_uttr["text"]):
        response = ""
        confidence = 0.0
    else:
        confidence = LINKTO_FOR_LONG_RESPONSE_CONFIDENCE
    if link["skill"] not in human_attr["used_links"]:
        human_attr["used_links"][link["skill"]] = []
    human_attr["used_links"][link["skill"]].append(link["phrase"])
    attr = {}
    return response, confidence, human_attr, bot_attr, attr


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time()
    dialogs = request.json["dialogs"]
    responses = []
    confidences = []
    human_attributes = []
    bot_attributes = []
    attributes = []

    topics, statuses, curr_news_samples = collect_topics_and_statuses(dialogs)
    topics = [remove_punct_and_articles(topic) for topic in topics]
    topics = np.array(topics)
    statuses = np.array(statuses)
    curr_news_samples = np.array(curr_news_samples)

    for dialog, curr_topic, curr_status, result in zip(dialogs, topics, statuses, curr_news_samples):
        logger.info(f"Composing answer for topic: {curr_topic} and status: {curr_status}.")
        logger.info(f"Result: {result}.")

        human_attr = {}
        human_attr["used_links"] = dialog["human"]["attributes"].get("used_links", defaultdict(list))
        human_attr["disliked_skills"] = dialog["human"]["attributes"].get("disliked_skills", [])
        human_attr["news_api_skill"] = dialog["human"]["attributes"].get("news_api_skill", {})
        human_attr["news_api_skill"]["discussed_news"] = human_attr["news_api_skill"].get("discussed_news", [])
        bot_attr = {}
        # the only difference is that result is already is a dictionary with news.

        lets_chat_about_particular_topic = if_chat_about_particular_topic(
            dialog["human_utterances"][-1], dialog["bot_utterances"][-1] if len(dialog["bot_utterances"]) else {}
        )
        curr_uttr = dialog["human_utterances"][-1]
        about_news = ({"News"} & set(get_topics(curr_uttr, which="cobot_topics"))) or re.search(
            NEWS_TEMPLATES, curr_uttr["text"].lower()
        )
        about_news = about_news and not re.search(FALSE_NEWS_TEMPLATES, curr_uttr["text"].lower())
        prev_bot_uttr_lower = dialog["bot_utterances"][-1]["text"].lower() if len(dialog["bot_utterances"]) > 0 else ""

        if lets_chat_about_particular_topic:
            prev_news_skill_output = get_skill_outputs_from_dialog(
                dialog["utterances"][-3:], skill_name="news_api_skill", activated=True
            )
            if result and len(prev_news_skill_output) == 0:
                # it was a lets chat about topic and we found appropriate news
                if curr_topic == "all":
                    if about_news:
                        response = OFFER_BREAKING_NEWS
                        confidence = DEFAULT_NEWS_OFFER_CONFIDENCE  # 1.0
                        attr = {
                            "news_status": OFFERED_BREAKING_NEWS_STATUS,
                            "news_topic": "all",
                            "can_continue": CAN_CONTINUE_PROMPT,
                            "curr_news": result,
                        }
                        if attr["curr_news"]["url"] not in human_attr["news_api_skill"]["discussed_news"]:
                            human_attr["news_api_skill"]["discussed_news"] += [attr["curr_news"]["url"]]
                    else:
                        response = ""
                        confidence = 0.0
                        attr = {}
                else:
                    response = SAY_TOPIC_SPECIFIC_NEWS.replace("TOPIC", curr_topic)
                    response = f"{response} {result['title']}.. {OFFER_MORE}"
                    confidence = LINKTO_CONFIDENCE
                    attr = {
                        "news_status": OFFERED_NEWS_DETAILS_STATUS,
                        "news_topic": curr_topic,
                        "curr_news": result,
                        "can_continue": CAN_CONTINUE_PROMPT,
                    }
                    if attr["curr_news"]["url"] not in human_attr["news_api_skill"]["discussed_news"]:
                        human_attr["news_api_skill"]["discussed_news"] += [attr["curr_news"]["url"]]
                responses.append(response)
                confidences.append(confidence)
                human_attributes.append(human_attr)
                bot_attributes.append(bot_attr)
                attributes.append(attr)
                continue
            else:
                responses.append("")
                confidences.append(0.0)
                human_attributes.append(human_attr)
                bot_attributes.append(bot_attr)
                attributes.append({})
                continue

        if result:
            logger.info("Topic: {}".format(curr_topic))
            logger.info("News found: {}".format(result))
            if curr_status == "headline":
                if len(dialog["human_utterances"]) > 0:
                    curr_uttr = dialog["human_utterances"][-1]
                else:
                    curr_uttr = {"text": ""}

                if OFFER_BREAKING_NEWS.lower() in prev_bot_uttr_lower and is_yes(curr_uttr):
                    response = f"Here it is: {result['title']}.. {OFFER_MORE}"
                    confidence = DEFAULT_NEWS_OFFER_CONFIDENCE
                    attr = {
                        "news_status": OFFERED_NEWS_DETAILS_STATUS,
                        "news_topic": curr_topic,
                        "curr_news": result,
                        "can_continue": MUST_CONTINUE,
                    }
                    if attr["curr_news"]["url"] not in human_attr["news_api_skill"]["discussed_news"]:
                        human_attr["news_api_skill"]["discussed_news"] += [attr["curr_news"]["url"]]
                elif curr_topic == "all":
                    prev_news_skill_output = get_skill_outputs_from_dialog(
                        dialog["utterances"][-3:], skill_name="news_api_skill", activated=True
                    )
                    if (
                        len(prev_news_skill_output) > 0
                        and prev_news_skill_output[-1].get("news_status", "") == OFFERED_NEWS_TOPIC_CATEGORIES_STATUS
                    ):
                        # topic was not detected
                        response = ""
                        confidence = 0.0
                        attr = {}
                    else:
                        response = f"Here is one of the latest news that I found: {result['title']}.. {OFFER_MORE}"
                        confidence = DEFAULT_NEWS_OFFER_CONFIDENCE
                        attr = {
                            "news_status": OFFERED_NEWS_DETAILS_STATUS,
                            "news_topic": curr_topic,
                            "curr_news": result,
                            "can_continue": MUST_CONTINUE,
                        }
                        if attr["curr_news"]["url"] not in human_attr["news_api_skill"]["discussed_news"]:
                            human_attr["news_api_skill"]["discussed_news"] += [attr["curr_news"]["url"]]
                else:
                    response = (
                        f"Here is one of the latest news on topic {curr_topic}: " f"{result['title']}.. {OFFER_MORE}"
                    )
                    confidence = DEFAULT_NEWS_OFFER_CONFIDENCE
                    attr = {
                        "news_status": OFFERED_NEWS_DETAILS_STATUS,
                        "news_topic": curr_topic,
                        "curr_news": result,
                        "can_continue": MUST_CONTINUE,
                    }
                    if attr["curr_news"]["url"] not in human_attr["news_api_skill"]["discussed_news"]:
                        human_attr["news_api_skill"]["discussed_news"] += [attr["curr_news"]["url"]]
            elif curr_status == "details":
                response = f"In details: {result['description']}. {ASK_OPINION}"
                confidence = DEFAULT_NEWS_DETAILS_CONFIDENCE
                attr = {
                    "news_status": OPINION_REQUEST_STATUS,
                    "news_topic": curr_topic,
                    "curr_news": result,
                    "can_continue": MUST_CONTINUE,
                }
                if attr["curr_news"]["url"] not in human_attr["news_api_skill"]["discussed_news"]:
                    human_attr["news_api_skill"]["discussed_news"] += [attr["curr_news"]["url"]]
            elif curr_status == "declined":
                # user declined to get latest news, topical news, or we did not find news request
                response, confidence, human_attr, bot_attr, attr = "", 0.0, {}, {}, {}
            else:
                prev_news_skill_output = get_skill_outputs_from_dialog(
                    dialog["utterances"][-3:], skill_name="news_api_skill", activated=True
                )
                curr_uttr = dialog["human_utterances"][-1]
                # status finished is here
                if len(prev_news_skill_output) > 0 and prev_news_skill_output[-1].get("news_status", "") not in [
                    OFFERED_NEWS_DETAILS_STATUS,
                    OFFERED_NEWS_TOPIC_CATEGORIES_STATUS,
                ]:
                    result = prev_news_skill_output[-1].get("curr_news", {})
                    # try to offer more news
                    topics_list = NEWS_TOPICS[:]
                    random.shuffle(topics_list)
                    offered_topics = []
                    for topic in topics_list:
                        curr_topic_result = get_news_for_current_entity(
                            topic, curr_uttr, human_attr["news_api_skill"]["discussed_news"]
                        )
                        if len(curr_topic_result) > 0:
                            offered_topics.append(topic)
                            logger.info("Topic: {}".format(topic))
                            logger.info("Result: {}".format(curr_topic_result))
                        if len(offered_topics) == 2:
                            break
                    if len(offered_topics) == 2:
                        # two topics with result news were found
                        response = (
                            f"{random.choice(WHAT_TYPE_OF_NEWS)} "
                            f"{offered_topics[0]} or {offered_topics[1].lower()}?"
                        )
                        confidence = WHAT_TYPE_OF_NEWS_CONFIDENCE
                        attr = {
                            "news_status": OFFERED_NEWS_TOPIC_CATEGORIES_STATUS,
                            "can_continue": CAN_CONTINUE_PROMPT,
                            "news_topic": " ".join(offered_topics),
                            "curr_news": result,
                        }
                        if attr["curr_news"]["url"] not in human_attr["news_api_skill"]["discussed_news"]:
                            human_attr["news_api_skill"]["discussed_news"] += [attr["curr_news"]["url"]]
                    else:
                        # can't find enough topics for the user to offer
                        response, confidence, human_attr, bot_attr, attr = link_to_other_skills(
                            human_attr, bot_attr, curr_uttr
                        )
                else:
                    # news was offered previously but the user refuse to get it
                    # or false news request was detected
                    response, confidence, human_attr, bot_attr, attr = "", 0.0, {}, {}, {}

        else:
            # no found news
            logger.info("No particular news found.")
            new_result = get_news_for_current_entity("all", curr_uttr, human_attr["news_api_skill"]["discussed_news"])
            if curr_topic != "all" and len(new_result.get("title", "")) > 0:
                logger.info("Offer latest news.")
                response = f"Sorry, I could not find some specific news. {OFFER_BREAKING_NEWS}"
                confidence = NOT_SPECIFIC_NEWS_OFFER_CONFIDENCE
                attr = {
                    "news_status": OFFERED_BREAKING_NEWS_STATUS,
                    "news_topic": "all",
                    "can_continue": MUST_CONTINUE,
                    "curr_news": new_result,
                }
                if attr["curr_news"]["url"] not in human_attr["news_api_skill"]["discussed_news"]:
                    human_attr["news_api_skill"]["discussed_news"] += [attr["curr_news"]["url"]]
            elif OFFER_BREAKING_NEWS.lower() in prev_bot_uttr_lower and is_yes(curr_uttr):
                logger.info("No latest news found.")
                response = (
                    "Sorry, seems like all the news slipped my mind. Let's chat about something else. "
                    "What do you want to talk about?"
                )
                confidence = NOT_SPECIFIC_NEWS_OFFER_CONFIDENCE
                attr = {"news_status": OFFERED_BREAKING_NEWS_STATUS, "can_continue": MUST_CONTINUE}
            else:
                response, confidence, human_attr, bot_attr, attr = "", 0.0, {}, {}, {}

        responses.append(response)
        confidences.append(confidence)
        human_attributes.append(human_attr)
        bot_attributes.append(bot_attr)
        attributes.append(attr)

    total_time = time() - st_time
    logger.info(f"news_api_skill exec time: {total_time:.3f}s")
    return jsonify(list(zip(responses, confidences, human_attributes, bot_attributes, attributes)))


@app.route("/healthz", methods=["GET"])
def healthz():
    return "OK", 200


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
