#!/usr/bin/env python

import json
import random
import common.dff.integration.context as int_ctx
from datetime import datetime
from df_engine.core import Actor, Context

INTENT_RESPONSES_PATH = "scenario/data/intent_response_phrases.json"


with open(INTENT_RESPONSES_PATH, "r") as fp:
    RESPONSES = json.load(fp)


def exit_respond(ctx: Context, actor: Actor, intention: str):
    response_phrases = RESPONSES[intention]
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
    utts = get_human_utterances(ctx, actor)
    response = random.choice(response_phrases).strip()  # Neutral response
    annotations = utts[-1]["annotations"]

    sentiment = int_ctx.get_human_sentiment(ctx, actor)
    offensiveness, is_badlisted = "", False
    try:
        offensiveness = annotations["cobot_offensiveness"]["text"]
    except KeyError:
        offensiveness = "non-toxic"
    try:
        is_badlisted = annotations["cobot_offensiveness"]["is_badlisted"] == "badlist"
    except KeyError:
        is_badlisted = False

    if len(utts) < 4:
        response = random.choice(apology_bye_phrases)
    elif sentiment == "positive":
        positive = ["I'm glad to help you! ", "Thanks for the chat! ", "Cool! "]
        response = random.choice(positive) + response
    elif offensiveness == "toxic" or is_badlisted or sentiment == "negative":
        response = random.choice(apology_bye_phrases)
    return response


def repeat_respond(ctx: Context, actor: Actor, intention: str):
    utterances_bot = int_ctx.get_bot_utterances(ctx, actor)
    utterances_human = get_human_utterances(ctx, actor)
    WHAT_BOT_PHRASES = ["did i say something confusing", "you sound shocked", "if you want me to repeat"]
    bot_phrases = [utt.get("text", "") if isinstance(utt, dict) else utt for utt in utterances_bot]
    if len(utterances_human) >= 2:
        responder_phrase = utterances_human[-2]["text"].lower()
        if any([bot_ptrn in responder_phrase for bot_ptrn in WHAT_BOT_PHRASES]):
            bot_utt = ""
            for bot_phrase in bot_phrases[::-1]:
                if bot_phrase != bot_phrases[-1]:
                    bot_utt = bot_phrase
                    break
        else:
            bot_utt = utterances_human[-2]["text"]
    else:
        bot_utt = ""
    return bot_utt if len(bot_utt) > 0 else "I did not say anything!"


def where_are_you_from_respond(ctx: Context, actor: Actor, intention: str):
    response_phrases = RESPONSES[intention]
    dialog = int_ctx.get_dialog(ctx, actor)
    human_profile_exists = "human" in dialog and "profile" in dialog["human"]

    already_known_user_property = None
    if human_profile_exists:
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


def random_respond(ctx: Context, actor: Actor, intention: str):
    response_phrases = RESPONSES[intention]
    dialog = int_ctx.get_dialog(ctx, actor)
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


def random_respond_with_question_asking(ctx: Context, actor: Actor, intention: str):
    utt = int_ctx.get_last_human_utterance(ctx, actor)
    response = random_respond(ctx, actor, intention)
    if "you" in utt:
        you = "you"
    else:
        you = "yours"
    response = f"{response}. And {you}?"
    return response


def what_time_respond(ctx: Context, actor: Actor, intention: str):
    time = datetime.utcnow()
    response = f"It is {time.hour} hours and {time.minute} minutes by U. T. C. What a time to be alive!"
    return response


def what_is_current_dialog_id_respond(ctx: Context, actor: Actor, intention: str):
    dialog = int_ctx.get_dialog(ctx, actor)
    dialog_id = dialog.get("dialog_id", "unknown")
    response = f"Dialog id is: {dialog_id}"
    return response


def get_respond_funcs():
    return {
        "exit": exit_respond,
        "repeat": repeat_respond,
        "where_are_you_from": where_are_you_from_respond,
        "get_dialog_id": what_is_current_dialog_id_respond,
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
    }


def get_human_utterances(ctx: Context, actor: Actor) -> list:
    return {} if ctx.validation else ctx.misc["agent"]["dialog"]["human_utterances"]
