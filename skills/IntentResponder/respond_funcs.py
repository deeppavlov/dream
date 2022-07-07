#!/usr/bin/env python

import random
from datetime import datetime

from common.utils import get_sentiment


def exit_respond(dialog, response_phrases):
    # goodbye_fix_phrases = ["goodbye", "bye", "bye bye", "alexa bye", "bye alexa", "goodbye alexa", "alexa bye bye"]
    apology_bye_phrases = [
        "Sorry, have a great day!",
        "Sorry to bother you, see you next time!",
        "My bad. Have a great time!",
        "Didn't mean to be rude. Talk to you next time.",
        "Sorry for interrupting you. Talk to you soon.",
        "Terribly sorry. Have a great day!",
        "Thought you wanted to chat. My bad. See you soon!",
        "Oh, sorry. Have a great day!",
    ]
    utt = dialog["utterances"][-1]
    response = random.choice(response_phrases).strip()  # Neutral response
    annotation = utt["annotations"]
    try:
        sentiment = get_sentiment(utt, probs=False)[0]
    except KeyError:
        sentiment = "neutral"
    # sentiment_confidence = annotation['cobot_sentiment']['confidence']
    try:
        offensiveness = annotation["cobot_offensiveness"]["text"]
    except KeyError:
        offensiveness = "non-toxic"
    # offensiveness_confidence = annotation['cobot_offensiveness']['confidence']
    try:
        is_badlisted = annotation["cobot_offensiveness"]["is_badlisted"] == "badlist"
    except KeyError:
        is_badlisted = False
    if len(dialog["utterances"]) < 4:
        response = random.choice(apology_bye_phrases)
    elif sentiment == "positive":
        positive = ["I'm glad to help you! ", "Thanks for the chat! ", "Cool! "]
        response = random.choice(positive) + response
    elif offensiveness == "toxic" or is_badlisted or sentiment == "negative":
        response = random.choice(apology_bye_phrases)
    return response


def repeat_respond(dialog, response_phrases):
    WHAT_BOT_PHRASES = ["did i say something confusing", "you sound shocked", "if you want me to repeat"]
    bot_phrases = [utt.get("text", "") if isinstance(utt, dict) else utt for utt in dialog["bot_utterances"]]
    if len(dialog["utterances"]) >= 2:
        responder_phrase = dialog["utterances"][-2]["text"].lower()
        if any([j in responder_phrase for j in WHAT_BOT_PHRASES]):
            bot_utt = ""
            for bot_phrase in bot_phrases[::-1]:
                if bot_phrase != bot_phrases[-1]:
                    bot_utt = bot_phrase
                    break
        else:
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
    if isinstance(response_phrases, dict):
        if dialog["seen"]:
            response = random.choice(response_phrases["last"]).strip()
        else:
            response = random.choice(response_phrases["first"]).strip()
    else:
        response = random.choice(response_phrases).strip()

    # TODO: somehow response sometimes is dict
    if type(response) == dict:
        if dialog["seen"]:
            response = random.choice(response["last"]).strip()
        else:
            response = random.choice(response["first"]).strip()
    return response


def random_respond_with_question_asking(dialog, response_phrases):
    utt = dialog["utterances"][-1]["text"]
    response = random_respond(dialog, response_phrases)
    if "you" in utt:
        you = "you"
    else:
        you = "yours"
    response = f"{response}. And {you}?"
    return response


def what_time_respond(dialog, response_phrases):
    time = datetime.utcnow()
    response = f"It is {time.hour} hours and {time.minute} minutes by U. T. C. What a time to be alive!"
    return response


def what_is_current_dialog_id_respond(dialog, response_phrases):
    dialog_id = dialog["dialog_id"]
    response = f"Dialog id is: {dialog_id}"
    return response


def get_respond_funcs():
    return {
        "exit": exit_respond,
        "repeat": repeat_respond,
        "where_are_you_from": where_are_you_from_respond,
        "who_made_you": random_respond,
        "what_is_your_name": random_respond,
        "what_is_your_job": random_respond,
        "what_can_you_do": random_respond,
        "what_time": what_time_respond,
        "dont_understand": random_respond,
        # "stupid": random_respond,
        "choose_topic": random_respond,
        "cant_do": random_respond,
        "tell_me_a_story": random_respond,
        "get_dialog_id": what_is_current_dialog_id_respond,
    }
