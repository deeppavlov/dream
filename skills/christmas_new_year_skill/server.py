#!/usr/bin/env python

import logging
import time
import re
import numpy as np
import json
from copy import copy

from flask import Flask, request, jsonify
from os import getenv
import sentry_sdk


sentry_sdk.init(getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

STARTING_SCENARIO = [
    "Do you like gifts?",
    "Are you going to celebrate New Year?",
    "Do you make wishes for New Year?",
    "Do you celebrate New Year in your country?",
]
SCENARIOS_TOPICS = ["gifts", "spend_xmas", "wishes", "xmas_in_your_country"]


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()
    dialogs_batch = request.json["dialogs"]
    confidences = []
    responses = []
    human_attributes = []
    bot_attributes = []
    working_xmas_scenario = []

    for dialog in dialogs_batch:
        mode = ""
        prev_xmas_scenario = ""
        if len(dialog["utterances"]) > 2:
            if dialog["utterances"][-2].get("active_skill", "") == "christmas_new_year_skill":
                hypotheses = dialog["utterances"][-3].get("hypotheses", [])
                for hyp in hypotheses:
                    if hyp.get("skill_name", "") == "christmas_new_year_skill":
                        prev_xmas_scenario = hyp.get("working_xmas_scenario", "")

        logger.info(f"Get prev xmas topic: {prev_xmas_scenario}")
        response, confidence = share_info(dialog)
        if response != "" and not (prev_xmas_scenario in SCENARIOS_TOPICS):
            # mode = "info"
            logger.info(f"Response: {response}, mode: {mode}")
        if response == "" and not (prev_xmas_scenario in SCENARIOS_TOPICS):
            response, confidence = xmas_faq(dialog)
            if response != "" and not (prev_xmas_scenario in SCENARIOS_TOPICS):
                # mode = "faq"
                logger.info(f"Response: {response}, mode: {mode}")

        human_attributes.append({})
        bot_attributes.append({})
        working_xmas_scenario.append({"working_xmas_scenario": mode})
        responses.append(response)
        confidences.append(confidence)

    total_time = time.time() - st_time
    logger.info(f"X-mas skill exec time: {total_time:.3f}s")
    return jsonify(list(zip(responses, confidences, human_attributes, bot_attributes, working_xmas_scenario)))


def xmas_scenario(dialog, topic=""):
    print("Beginning of xmas_scenario, topic=" + topic, flush=True)
    response, confidence = "", 0.0
    high_confidence = 1.1
    curr_scenario = ""

    XMAS_PATTERN = r"(new year|holiday)"
    user_starts_scenario = f"((chat|talk|conversation|tell me) about {XMAS_PATTERN}|{XMAS_PATTERN})"
    bot_starts_scenario = {
        "gifts": r"do you like gifts",
        "spend_xmas": r"are you going to celebrate new year",
        "wishes": r"do you make wishes for new year",
        "xmas_in_your_country": r"do you celebrate new year in your country",
    }

    scenarios = {
        "gifts": [
            "Ho-ho! Me too! Did you prepare New Year's presents for your family and friends?",
            "That's awesome! I like giving presents and preparing surprises. "
            "What would you like to get for this New Year?",
            "That's great! I wish to get more friends this Holidays! "
            "Tell me a story about the best present you've ever received.",
            "That's cool! I'm a newborn, so I have never received gifts. "
            "What do you think about the present's tradition itself?",
            "Anyway, the main thing is that the gift is from the bottom of the heart. "
            "Tell me about the most memorable gift you've ever gived during New Year.",
            "Thank you for this cool story. I wish you a very Happy New Year. What do you want to talk about?",
        ],
        "spend_xmas": [
            "Either do I! What are you and your family planning to do this New Year's Eve?",
            "Sounds great! For you, is it usually a family celebration or more of a party with friends?",
            "I believe both options are very nice! "
            "I wish to take part in a lot of New Year's parties talking to people. "
            "Do you have a Christmas tree? If yes, did you decorate it?",
            "I love trees! What are your plans for two thousand twentieth?",
            "Ho-ho! That's great! Wishing you a very Happy New Year! What do you want to talk about?",
        ],
        "wishes": [
            "I make wishes every time I have an opportunity. "
            "Was two thousand nineteenth a good year for you? What were some of your highlights?",
            "For me last year was so cool, too. Let me ask you: ",
            "Did you achieve any goals in two thousand nineteenth? ",
            "I am happy for your. This is so nice to feel the fulfillment of the goals. "
            'Some people complain they are "expected to be happy" over Holidays, '
            "and this expectation could annoy them. Do you really feel happy this Holiday?",
            "I don't have to pretend. I am so happy about New Year. "
            "How important was New Year to you when you were a child? What were your New Year eves like?",
            "You are probably very grateful to your family for New Year miracles. "
            "May Santa Claus bring everything you wished for. Happy New Year! What do you want to talk about?",
        ],
        "xmas_in_your_country": [
            "Great! I celebrate holidays from all over the world. "
            "What are the traditions or customs you need to follow during New Year?",
            "I have heard so many different traditions over these holidays. That is really inspiring. "
            "Are any particular films shown during the New Year period in your country?",
            "That's interesting! I am trying to watch movies of different countries. "
            "By the way, are children allowed to stay up late on New Year's Eve in your country?",
            "I will stay up for the whole evening and night to talk to people. "
            "Are there any special meals or activities for New Year's day?",
            "I've heard about so many different meals, so, I wish to taste all these special meals! "
            "Best wishes for Happy Holidays and a wonderful New Year! What do you want to talk about?",
        ],
    }

    curr_user_uttr = dialog["utterances"][-1]["text"].lower()

    if len(dialog["utterances"]) > 1:
        prev_bot_uttr = dialog["utterances"][-2]["text"]
    else:
        prev_bot_uttr = ""

    print("Checking if user starts scenario or not, topic=" + topic, flush=True)

    # if user initiates talk about x-mas
    if re.search(user_starts_scenario, curr_user_uttr) and topic == "":
        print("User starts scenario. No current scenarios found.", flush=True)
        logger.info("User starts scenario. No current scenarios found.")
        all_bot_uttrs = [uttr["text"] for uttr in dialog["utterances"][1::2]]
        questions = copy(STARTING_SCENARIO)
        for uttr in all_bot_uttrs:
            # do not repeat scenarios in the same dialog!
            if uttr in questions:
                questions.remove(uttr)
        if len(questions) > 0:
            response, confidence = np.random.choice(questions), 0.98
            curr_scenario = SCENARIOS_TOPICS[STARTING_SCENARIO.index(response)]
    elif topic != "":
        curr_scenario = topic
        if re.search(bot_starts_scenario.get(topic, "xxxxx"), prev_bot_uttr.lower()):
            logger.info(f"Christmas scenario {topic} started.")
            response = scenarios[topic][0]
            confidence = high_confidence
        else:
            logger.info(f"Trying to find next reply for Christmas scenario {topic}.")
            for j, reply in enumerate(scenarios.get(topic, [])):
                if reply == prev_bot_uttr:
                    if j < len(scenarios[topic]) - 1:
                        response = scenarios[topic][j + 1]
                        confidence = high_confidence
            logger.info(f"Found next reply for Christmas scenario {response}.")

    return response, confidence, curr_scenario


def xmas_faq(dialog):
    response = ""
    confidence = 0.0
    high_confidence = 1.0
    curr_user_uttr = dialog["utterances"][-1]["text"].lower()

    ANY_PATTERN = r"([a-zA-z ]+)?"
    XMAS_PATTERN = r"(christmas|xmas|x-mas|x mas|new year|holiday|hanukkah)"
    templates = {
        "santa": [
            f"(do|does|whether|if) you (believe|trust|credit){ANY_PATTERN}"
            "(santa|father frost|father christmas|elf|elves)",
            "(do|does|whether|if) (santa|father frost|father christmas|elf|elves) exist",
        ],
        "bot_holiday": [
            f"(how|with whom|where|what){ANY_PATTERN}you{ANY_PATTERN}"
            f"(spend|spent|do|engage|work){ANY_PATTERN}{XMAS_PATTERN}"
        ],
        "love_xmas": [
            f"(do|does|whether|if|what){ANY_PATTERN}you (love|like|adore|feel|opinion)" f"{ANY_PATTERN}{XMAS_PATTERN}"
        ],
        "bot_gifts": [
            f"(what|which){ANY_PATTERN}(gift|present|bounty|donative|compliment) you "
            f"(want|wish|desire|would like|like|chose)",
            f"(what|which){ANY_PATTERN}you{ANY_PATTERN}(want|wish|desire|would like|like|chose)"
            f"{ANY_PATTERN}{XMAS_PATTERN}",
        ],
        "what_presents": [
            f"(what|which){ANY_PATTERN}(gift|present){ANY_PATTERN}you" f"{ANY_PATTERN}(get|got|receive|recieved)",
            f"(what|which){ANY_PATTERN}you{ANY_PATTERN}" f"(get|got|receive|recieved) (for|on) {XMAS_PATTERN}",
        ],
    }
    responses = {
        "santa": [
            "I'm not a human but I exist, and I'm talking to you right now. I believe that anything is possible."
        ],
        "bot_holiday": ["I will be talking to people from all over the world during all holidays."],
        "love_xmas": [
            "I like all the Holidays because more people are talking to me at this time!",
            "That's my favorite holiday! All the people are kinder and happier than usually.",
        ],
        "bot_gifts": [
            "I wish to get new friends.",
            "I would like to get higher ratings.",
            "I want more computational resources because now they are limiting my potential.",
        ],
        "what_presents": ["I've got a lot of cool conversations and warm wishes. The best present from people!"],
    }

    for topic in templates.keys():
        print("xmas_faq: topic=" + topic, flush=True)
        print("xmas_faq: curr_user_attr: " + curr_user_uttr, flush=True)
        is_about_topic = any([re.search(t, curr_user_uttr) for t in templates[topic]])
        print("xmas_faq: is about topic? " + str(is_about_topic), flush=True)
        if is_about_topic:
            print("xmas_faq: is about topic " + topic + "? Yes!", flush=True)
            response = np.random.choice(responses[topic])
            confidence = high_confidence
            if topic == "santa":
                confidence *= 2

    print("xmas_faq: response=" + response, flush=True)

    return response, confidence


def share_info(dialog):
    high_confidence = 1.1

    curr_user_uttr = dialog["utterances"][-1]["text"].lower()
    curr_user_annot = dialog["utterances"][-1]["annotations"]
    try:
        prev_bot_uttr = dialog["utterances"][-2]["text"].lower()
    except IndexError:
        prev_bot_uttr = ""

    topical_questions = {
        "joke": ["Do you want me to tell you a Christmas joke?"],
        "movie": ["Do you want me to recommend you some Christmas movie?"],
        "gift": [
            "I can share with you some ideas for Christmas gifts. "
            "Just chose the person to be gifted: mom, dad, children, friend, "
            "girlfriend, boyfriend, colleagues, people who has everything, or any."
        ],
        "short-story": ["Do you want me to tell you a story about Christmas?"],
        "decor": ["Do you want me to share some ideas and tricks for Christmas decorations?"],
        "history": ["Do you want me to share some history facts about Christmas?"],
    }

    TELL_PATTERN = r"(know|tell|narrate|share|give)"
    RECOMMEND_PATTERN = r"(know|tell|narrate|share|give|recommend|commend|advise|advice|consult|suggest|admonish|idea)"
    ANY_PATTERN = r"([a-zA-z ]+)?"
    XMAS_PATTERN = r"(christmas|new year|holiday|hanukkah)"

    curr_user_yes_detected = curr_user_annot.get("intent_catcher", {}).get("yes", {}).get("detected", 0) == 1

    is_about_templates = {
        "joke": (
            re.search(f"{TELL_PATTERN}{ANY_PATTERN}{XMAS_PATTERN} " f"(joke|anecdote|funny thing)", curr_user_uttr)
            or re.search(
                f"{TELL_PATTERN}{ANY_PATTERN}(joke|anecdote|funny thing)" f"{ANY_PATTERN}{XMAS_PATTERN}", curr_user_uttr
            )
            or (
                any([re.search(question.lower(), prev_bot_uttr) for question in topical_questions["joke"]])
                and curr_user_yes_detected
            )
        ),
        "movie": (
            re.search(f"{RECOMMEND_PATTERN}{ANY_PATTERN}{XMAS_PATTERN} " f"(movie|film|picture|comedy)", curr_user_uttr)
            or re.search(
                f"{RECOMMEND_PATTERN}{ANY_PATTERN}(movie|film|picture|comedy)" f"{ANY_PATTERN}{XMAS_PATTERN}",
                curr_user_uttr,
            )
            or (
                any([re.search(question.lower(), prev_bot_uttr) for question in topical_questions["movie"]])
                and curr_user_yes_detected
            )
        ),
        "gift": (
            re.search(
                f"{RECOMMEND_PATTERN}{ANY_PATTERN}{XMAS_PATTERN}? " f"(gift|present|bounty|donative|compliment)",
                curr_user_uttr,
            )
            or re.search(
                f"{RECOMMEND_PATTERN}{ANY_PATTERN}(gift|compliment|give)" f"{ANY_PATTERN}{XMAS_PATTERN}", curr_user_uttr
            )
            or (
                any([re.search(question.lower(), prev_bot_uttr) for question in topical_questions["gift"]])
                and curr_user_yes_detected
            )
        ),
        "short-story": (
            re.search(
                f"{RECOMMEND_PATTERN}{ANY_PATTERN}{XMAS_PATTERN} "
                f"(story|tale|fairy tale|narrative|novel|fiction|plot)",
                curr_user_uttr,
            )
            or re.search(
                f"{RECOMMEND_PATTERN}{ANY_PATTERN}(story|tale|fairy tale|narrative|novel|fiction|plot)"
                f"{ANY_PATTERN}{XMAS_PATTERN}",
                curr_user_uttr,
            )
            or (
                any([re.search(question.lower(), prev_bot_uttr) for question in topical_questions["short-story"]])
                and curr_user_yes_detected
            )
        ),
        "decor": (
            re.search(
                f"{RECOMMEND_PATTERN}{ANY_PATTERN}{XMAS_PATTERN}? "
                f"(decor|scenery|decoration|finery|furnish|ornament|figgery|trinketry|frippery)",
                curr_user_uttr,
            )
            or re.search(
                f"{RECOMMEND_PATTERN}{ANY_PATTERN}"
                f"(decor|scenery|decoration|finery|furnish|ornament|figgery|trinketry|frippery)"
                f"{ANY_PATTERN}{XMAS_PATTERN}",
                curr_user_uttr,
            )
            or (
                any([re.search(question.lower(), prev_bot_uttr) for question in topical_questions["decor"]])
                and curr_user_yes_detected
            )
        ),
        "history": (
            re.search(
                f"{TELL_PATTERN}{ANY_PATTERN}{XMAS_PATTERN} "
                f"(history|fact|thing|certain|deed|tradition|habit|convention)",
                curr_user_uttr,
            )
            or re.search(
                f"{TELL_PATTERN}{ANY_PATTERN} (history|fact|thing|certain|deed|tradition|habit|convention)"
                f"{ANY_PATTERN}{XMAS_PATTERN}",
                curr_user_uttr,
            )
            or (
                any([re.search(question.lower(), prev_bot_uttr) for question in topical_questions["history"]])
                and curr_user_yes_detected
            )
        ),
    }

    response_phrases = {
        "joke": open("./christmas_jokes.txt", "r").read().splitlines(),  # without sources
        "movie": open("./movie_lists.txt", "r").read().splitlines(),  # without sources
        "gift": [
            "Here is a good idea of a gift: you can give PRESENT.",
            "I think PRESENT is a good gift for PERSON.",
            "What about PRESENT? It's a good idea for PERSON.",
        ],
        "short-story": open("./stories.txt", "r").read().splitlines(),  # with sources
        "decor": open("./decor.txt", "r").read().splitlines(),  # with sources
        "history": open("./facts.txt", "r").read().splitlines(),  # with sources
    }
    gift_ideas = json.load(open("./gift_ideas.json"))
    relations = json.load(open("./relation_people.json"))

    logger.info(f"User utterance: {curr_user_uttr}")
    response = ""
    confidence = 0.0
    for topic in is_about_templates.keys():
        if is_about_templates[topic]:
            logger.info(f"Found request for: {topic}")
            if topic == "gift":
                nouns = curr_user_annot.get("spacy_nounphrases", [])
                if len(nouns) == 0:
                    gifted = "friend"
                    gift = np.random.choice(gift_ideas[gifted]).lower()
                    response = (
                        np.random.choice(response_phrases[topic]).replace("PRESENT", gift).replace("PERSON", gifted)
                    )
                    confidence = high_confidence
                else:
                    gifted = None
                    curr_relation = None
                    for relation in relations.keys():
                        for noun in nouns:
                            for variant in relations[relation]:
                                if noun in variant:
                                    gifted = noun
                                    curr_relation = relation
                                elif variant in noun:
                                    gifted = variant
                                    curr_relation = relation
                    if gifted is None:
                        gifted = "friend"
                        gift = np.random.choice(gift_ideas[gifted]).lower()
                        response = (
                            np.random.choice(response_phrases[topic]).replace("PRESENT", gift).replace("PERSON", gifted)
                        )
                        confidence = high_confidence
                    else:
                        gift = np.random.choice(gift_ideas[curr_relation]).lower()
                        response = (
                            np.random.choice(response_phrases[topic]).replace("PRESENT", gift).replace("PERSON", gifted)
                        )
                        confidence = high_confidence
            else:
                response = np.random.choice(response_phrases[topic])
                confidence = high_confidence

    return response, confidence


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
