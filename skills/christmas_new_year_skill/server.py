#!/usr/bin/env python

import logging
import time
import re
import numpy as np
import json

from flask import Flask, request, jsonify
from os import getenv
import sentry_sdk


sentry_sdk.init(getenv('SENTRY_DSN'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.route("/respond", methods=['POST'])
def respond():
    st_time = time.time()
    dialogs_batch = request.json["dialogs"]
    confidences = []
    responses = []

    for dialog in dialogs_batch:
        response, confidence = share_info(dialog)
        if response == "":
            response, confidence = xmas_faq(dialog)

        responses.append(response)
        confidences.append(confidence)

    total_time = time.time() - st_time
    logger.info(f'X-mas skill exec time: {total_time:.3f}s')
    return jsonify(list(zip(responses, confidences)))


def xmas_faq(dialog):
    response = ""
    confidence = 0.0
    high_confidence = 1.0
    curr_user_uttr = dialog["utterances"][-1]["text"].lower()

    ANY_PATTERN = r"([a-zA-z ]+)?"
    XMAS_PATTERN = r"(christmas|new year|holiday|hanukkah)"
    templates = {
        "santa": [f"(do|does|whether|if) you (believe|trust|credit){ANY_PATTERN}"
                  f"(santa|father frost|father christmas|elf|elves)",
                  f"(do|does|whether|if) (santa|father frost|father christmas|elf|elves) exist"],
        "bot_holiday": [f"(how|with whom|where|what){ANY_PATTERN}you{ANY_PATTERN}"
                        f"(spend|spent|do|engage|work){ANY_PATTERN}{XMAS_PATTERN}"],
        "love_xmas": [f"(do|does|whether|if|what){ANY_PATTERN}you (love|like|adore|feel|opinion)"
                      f"{ANY_PATTERN}{XMAS_PATTERN}"],
        "bot_gifts": [f"(what|which){ANY_PATTERN}(gift|present|bounty|donative|compliment) you "
                      f"(want|wish|desire|would like|like|chose)",
                      f"(what|which){ANY_PATTERN}you{ANY_PATTERN}(want|wish|desire|would like|like|chose)"
                      f"{ANY_PATTERN}{XMAS_PATTERN}"]
    }
    responses = {
        "santa": ["I'm not a human but I exist, and I'm talking to you right now. I believe that anything is possible."
                  ],
        "bot_holiday": ["I will be talking to people from all over the world during all holidays."],
        "love_xmas": ["I like all the Holidays because more people are talking to me at this time!",
                      "That's my favorite holiday! All the people are kinder and happier than usually."],
        "bot_gifts": ["I wish to get new friends.", "I would like to get higher ratings.",
                      "I want more computational resources because now they are limiting my potential."]
    }

    for topic in templates.keys():
        is_about_topic = any([re.search(t, curr_user_uttr) for t in templates[topic]])
        if is_about_topic:
            response = np.random.choice(responses[topic])
            confidence = high_confidence
            if topic == "santa":
                confidence *= 2

    return response, confidence


def share_info(dialog):
    high_confidence = 1.1

    curr_user_uttr = dialog["utterances"][-1]["text"].lower()
    curr_user_annot = dialog["utterances"][-1]["annotations"]
    try:
        prev_bot_uttr = dialog["utterances"][-2]["text"].lower()
    except IndexError:
        prev_bot_uttr = ""

    topical_questions = {"joke": ["Do you want me to tell you a Christmas joke?"],
                         "movie": ["Do you want me to recommend you some Christmas movie?"],
                         "gift": ["I can share with you some ideas for Christmas gifts. "
                                  "Just chose the person to be gifted: mom, dad, children, friend, "
                                  "girlfriend, boyfriend, colleagues, people who has everything, or any."],
                         "short-story": ["Do you want me to tell you a story about Christmas?"],
                         "decor": ["Do you want me to share some ideas and tricks for Christmas decorations?"],
                         "history": ["Do you want me to share some history facts about Christmas?"]
                         }

    TELL_PATTERN = r"(know|tell|narrate|share|give)"
    RECOMMEND_PATTERN = r"(know|tell|narrate|share|give|recommend|commend|advise|advice|consult|suggest|admonish|idea)"
    ANY_PATTERN = r"([a-zA-z ]+)?"
    XMAS_PATTERN = r"(christmas|new year|holiday|hanukkah)"

    curr_user_yes_detected = curr_user_annot.get("intent_catcher", {}).get("yes", {}).get("detected", 0) == 1

    is_about_templates = {
        "joke": (re.search(f"{TELL_PATTERN}{ANY_PATTERN}{XMAS_PATTERN} "
                           f"(joke|anecdote|funny thing)", curr_user_uttr) or re.search(
            f"{TELL_PATTERN}{ANY_PATTERN}(joke|anecdote|funny thing)"
            f"{ANY_PATTERN}{XMAS_PATTERN}", curr_user_uttr) or (
                any([re.search(question.lower(), prev_bot_uttr) for question in topical_questions["joke"]]
                    ) and curr_user_yes_detected)),
        "movie": (re.search(f"{RECOMMEND_PATTERN}{ANY_PATTERN}{XMAS_PATTERN} "
                            f"(movie|film|picture|comedy)", curr_user_uttr) or re.search(
            f"{RECOMMEND_PATTERN}{ANY_PATTERN}(movie|film|picture|comedy)"
            f"{ANY_PATTERN}{XMAS_PATTERN}", curr_user_uttr) or (
                any([re.search(question.lower(), prev_bot_uttr) for question in topical_questions["movie"]]
                    ) and curr_user_yes_detected)),
        "gift": (re.search(f"{RECOMMEND_PATTERN}{ANY_PATTERN}{XMAS_PATTERN}? "
                           f"(gift|present|bounty|donative|compliment)", curr_user_uttr) or re.search(
            f"{RECOMMEND_PATTERN}{ANY_PATTERN}(gift|compliment|give)"
            f"{ANY_PATTERN}{XMAS_PATTERN}", curr_user_uttr) or (
                any([re.search(question.lower(), prev_bot_uttr) for question in topical_questions["gift"]]
                    ) and curr_user_yes_detected)),
        "short-story": (re.search(f"{RECOMMEND_PATTERN}{ANY_PATTERN}{XMAS_PATTERN} "
                                  f"(story|tale|fairy tale|narrative|novel|fiction|plot)", curr_user_uttr) or re.search(
            f"{RECOMMEND_PATTERN}{ANY_PATTERN}(story|tale|fairy tale|narrative|novel|fiction|plot)"
            f"{ANY_PATTERN}{XMAS_PATTERN}", curr_user_uttr) or (
                any([re.search(question.lower(), prev_bot_uttr) for question in topical_questions["short-story"]]
                    ) and curr_user_yes_detected)),
        "decor": (re.search(f"{RECOMMEND_PATTERN}{ANY_PATTERN}{XMAS_PATTERN}? "
                            f"(decor|scenery|decoration|finery|furnish|ornament|figgery|trinketry|frippery)",
                            curr_user_uttr) or re.search(
            f"{RECOMMEND_PATTERN}{ANY_PATTERN}"
            f"(decor|scenery|decoration|finery|furnish|ornament|figgery|trinketry|frippery)"
            f"{ANY_PATTERN}{XMAS_PATTERN}", curr_user_uttr) or (
                any([re.search(question.lower(), prev_bot_uttr) for question in topical_questions["decor"]]
                    ) and curr_user_yes_detected)),
        "history": (re.search(f"{TELL_PATTERN}{ANY_PATTERN}{XMAS_PATTERN} "
                              f"(history|fact|thing|certain|deed|tradition|habit|convention)",
                              curr_user_uttr) or re.search(
            f"{TELL_PATTERN}{ANY_PATTERN} (history|fact|thing|certain|deed|tradition|habit|convention)"
            f"{ANY_PATTERN}{XMAS_PATTERN}", curr_user_uttr) or (
                any([re.search(question.lower(), prev_bot_uttr) for question in topical_questions["history"]]
                    ) and curr_user_yes_detected)),
    }

    response_phrases = {"joke": open("./christmas_jokes.txt", "r").read().splitlines(),  # without sources
                        "movie": open("./movie_lists.txt", "r").read().splitlines(),  # without sources
                        "gift": ["Here is a good idea of a gift: you can give PRESENT.",
                                 "I think PRESENT is a good gift for PERSON.",
                                 "What about PRESENT? It's a good idea for PERSON."],
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
                nouns = curr_user_annot.get("cobot_nounphrases", [])
                if len(nouns) == 0:
                    gifted = "friend"
                    gift = np.random.choice(gift_ideas[gifted]).lower()
                    response = np.random.choice(
                        response_phrases[topic]).replace("PRESENT", gift).replace("PERSON", gifted)
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
                        response = np.random.choice(
                            response_phrases[topic]).replace("PRESENT", gift).replace("PERSON", gifted)
                        confidence = high_confidence
                    else:
                        gift = np.random.choice(gift_ideas[curr_relation]).lower()
                        response = np.random.choice(
                            response_phrases[topic]).replace("PRESENT", gift).replace("PERSON", gifted)
                        confidence = high_confidence
            else:
                response = np.random.choice(response_phrases[topic])
                confidence = high_confidence

    return response, confidence


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=3000)
