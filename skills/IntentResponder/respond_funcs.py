#!/usr/bin/env python

import random
from datetime import datetime


def exit_respond(utt, response_phrases):
    response = random.choice(response_phrases).strip()  # Neutral response
    annotation = utt["annotation"]
    try:
        sentiment = annotation["sentiment_classification"]["text"]
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
    elif sentiment == "negative":
        response = "I apologize for dissapointing you, I'm still learning. " + response
    return response


def repeat_respond(utt, response_phrases):
    return utt["bot_sentence"] if len(utt["bot_sentence"]) > 0 else "I did not say anything!"


def where_are_you_from_respond(utt, response_phrases):
    response = random.choice(response_phrases).strip()
    return response


def random_respond(utt, response_phrases):
    response = random.choice(response_phrases).strip()
    return response


def random_respond_with_question_asking(utt, response_phrases):
    response = random_respond(utt, response_phrases)
    if 'you' in utt:
        you = 'you'
    else:
        you = 'yours'
    response = f"{response}. And {you}?"
    return response


def what_time_respond(utt, response_phrases):
    time = datetime.utcnow()
    response = f"It is {time.hour} hours and {time.minute} minutes by UTC. What a time to be alive!"
    return response


def get_respond_funcs():
    return {
        "exit": exit_respond,
        "repeat": repeat_respond,
        "where_are_you_from": random_respond,
        "who_made_you": random_respond,
        "what_is_your_name": random_respond,
        "what_is_your_job": random_respond,
        "what_can_you_do": random_respond,
        "what_time": what_time_respond,
        "dont_understand": random_respond
    }
