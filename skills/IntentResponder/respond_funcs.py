#!/usr/bin/env python

import random
from datetime import datetime


def exit_respond(dialog, response_phrases):
    # goodbye_fix_phrases = ["goodbye", "bye", "bye bye", "alexa bye", "bye alexa", "goodbye alexa", "alexa bye bye"]
    utt = dialog["utterances"][-1]
    response = random.choice(response_phrases).strip()  # Neutral response
    annotation = utt["annotations"]
    try:
        sentiment = annotation.get("sentiment_classification", {}).get("text", [""])[0]
    except KeyError:
        sentiment = "neutral"
    # sentiment_confidence = annotation['cobot_sentiment']['confidence']
    try:
        offensiveness = annotation["cobot_offensiveness"]["text"]
    except KeyError:
        offensiveness = "non-toxic"
    # offensiveness_confidence = annotation['cobot_offensiveness']['confidence']
    try:
        is_blacklisted = annotation["cobot_offensiveness"]["is_blacklisted"] == "blacklist"
    except KeyError:
        is_blacklisted = False

    if sentiment == "positive":
        positive = ["I'm glad to help you! ", "Thanks for the chat! ", "Cool! "]
        response = random.choice(positive) + response
    elif offensiveness == "toxic" or is_blacklisted:
        response = "I'm sorry if i dissapointed you, but there is no need to be rude. " + response
    # elif sentiment == "negative" and utt["text"] not in goodbye_fix_phrases:
    #     response = "I apologize for dissapointing you, I'm still learning. " + response
    return response


def repeat_respond(dialog, response_phrases):
    if len(dialog["utterances"]) >= 2:
        bot_utt = dialog["utterances"][-2]["text"]
    else:
        bot_utt = ""
    return bot_utt if len(bot_utt) > 0 else "I did not say anything!"


def where_are_you_from_respond(dialog, response_phrases):
    already_known_user_property = dialog["human"]["profile"].get("homeland", None)
    if already_known_user_property is None:
        response = random.choice(response_phrases).strip() + " Where are you from?"
    else:
        already_known_user_property = dialog["human"]["profile"].get("location", None)
        if already_known_user_property is None:
            response = random.choice(response_phrases).strip() + " What is your location?"
        else:
            response = random.choice(response_phrases).strip()
    return response


def random_respond(dialog, response_phrases):
    response = random.choice(response_phrases).strip()
    return response


def random_respond_with_question_asking(dialog, response_phrases):
    utt = dialog["utterances"][-1]["text"]
    response = random_respond(dialog, response_phrases)
    if 'you' in utt:
        you = 'you'
    else:
        you = 'yours'
    response = f"{response}. And {you}?"
    return response


def what_time_respond(dialog, response_phrases):
    time = datetime.utcnow()
    response = f"It is {time.hour} hours and {time.minute} minutes by UTC. What a time to be alive!"
    return response


def what_is_your_name_respond(dialog, response_phrases):
    already_known_user_property = dialog["human"]["profile"].get("name", None)
    if already_known_user_property is None:
        response = random.choice(response_phrases).strip() + " What is your name?"
    else:
        response = random.choice(response_phrases).strip()
    return response


def get_respond_funcs():
    return {
        "exit": exit_respond,
        "repeat": repeat_respond,
        "where_are_you_from": where_are_you_from_respond,
        "who_made_you": random_respond,
        "what_is_your_name": what_is_your_name_respond,
        "what_is_your_job": random_respond,
        "what_can_you_do": random_respond,
        "what_time": what_time_respond,
        "dont_understand": random_respond
    }
