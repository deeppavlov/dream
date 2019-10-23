#!/usr/bin/env python

import random


def exit_respond(utt, response_phrases):
    response = random.choice(response_phrases).strip()  # Neutral response
    annotation = utt['annotation']
    try:
        sentiment = annotation['cobot_sentiment']['text']
    except KeyError:
        sentiment = 'neutral'
    # sentiment_confidence = annotation['cobot_sentiment']['confidence']
    try:
        offensiveness = annotation['cobot_offensiveness']['text']
    except KeyError:
        offensiveness = 'non-toxic'
    # offensiveness_confidence = annotation['cobot_offensiveness']['confidence']
    try:
        is_blacklisted = annotation['cobot_offensiveness']['is_blacklisted'] == 'blacklist'
    except KeyError:
        is_blacklisted = False

    if sentiment == 'positive':
        positive = ["I'm glad to help you! ", "Thanks for the chat! ", "Cool! "]
        response = random.choice(positive) + response
    elif offensiveness == 'toxic' or is_blacklisted:
        response = "I'm sorry if i dissapointed you, but there is no need to be rude. " + response
    elif sentiment == 'negative':
        response = "I apologize for dissapointing you, I'm still learning. " + response
    return response


def repeat_respond(utt, response_phrases):
    return utt['bot_sentence'] if len(utt['bot_sentence']) > 0 else "I did not say anything!"


def where_are_you_from_respond(utt, response_phrases):
    response = random.choice(response_phrases).strip()
    return response


def who_made_you_respond(utt, response_phrases):
    response = random.choice(response_phrases).strip()
    return response


def lets_chat_respond(utt, response_phrases):
    response = random.choice(response_phrases).strip()
    return response


def what_is_your_name_respond(utt, response_phrases):
    response = random.choice(response_phrases).strip()
    return response


def what_is_your_job_respond(utt, response_phrases):
    response = random.choice(response_phrases).strip()
    return response


def what_can_you_do_respond(utt, response_phrases):
    response = random.choice(response_phrases).strip()
    return response


def get_respond_funcs():
    return {
        "exit": exit_respond,
        "repeat": repeat_respond,
        "where_are_you_from": where_are_you_from_respond,
        "who_made_you": who_made_you_respond,
        "what_is_your_name": what_is_your_name_respond,
        "what_is_your_job": what_is_your_job_respond,
        "what_can_you_do": what_can_you_do_respond
    }
