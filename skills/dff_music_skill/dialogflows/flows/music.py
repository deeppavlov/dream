# %%
import json
import logging
import os
import random
import re

# from CoBotQA.cobotqa_service import send_cobotqa
from enum import Enum, auto

import sentry_sdk

import common.dialogflow_framework.stdm.dialogflow_extention as dialogflow_extention
import common.dialogflow_framework.utils.state as state_utils
import dialogflows.scopes as scopes
from common.universal_templates import if_lets_chat_about_topic, COMPILE_WHAT_TO_TALK_ABOUT
from common.utils import get_intents, is_yes, is_no


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))


logger = logging.getLogger(__name__)


MUST_CONTINUE_CONFIDENCE = 0.98
CANNOT_CONTINUE_CONFIDENCE = 0.0

with open("music_data.json", "r") as f:
    MUSIC_DATA = json.load(f)

music_words_re = re.compile(
    r"(music)|(musics)|(song)|(rap)|(rock)|(melody)|(symphony)|(pop)|\
    (jazz)|(funk)|(blues)|(hip hop)|(folk)|(trance)|(reggae)|(artist)|(heavy metal)",
    re.IGNORECASE,
)
like_re = re.compile(r"what ((songs)|(music)|(song)|(artist)|(singer)) do you ((like)|(listen)|(love)|(prefer))")
dont_know_re = re.compile(r"((dont)|(doesnt)|(do not)|(does not)|(don't)|(doesn't)) know")
i_like_re = re.compile(r"((like)|(love)|(adore)|(listen to)|(prefer))", re.IGNORECASE)
music_request_re = re.compile(r"(alexa\, music)|(music)", re.IGNORECASE)
genre_re = re.compile(r"(genre)")
song_re = re.compile(r"(song)|(album)")
band_re = re.compile(r"(singer)|(artist)|(perfomer)|(band)|(orchestra)")
what_listen_re = re.compile("what ((((should)|(can)|(may)) I listen)|(you suggest listening))")
# what_music = re.compile(r"(what should i|what do you suggest me to) (cook|make for dinner)"
#                        "( tonight| today| tomorrow){0,1}", re.IGNORECASE)


class State(Enum):
    USR_START = auto()
    #
    SYS_LETS_TALK_ABOUT = auto()
    SYS_MUSIC = auto()
    SYS_MENTION = auto()
    SYS_ASKS = auto()
    USR_MUSIC = auto()
    USR_TALK_MUSIC = auto()
    USR_WHAT_MUSIC = auto()
    USR_FAV = auto()
    #
    SYS_MUSIC_NO = auto()
    SYS_MUSIC_YES = auto()
    USR_MUSIC_YES = auto()
    #
    SYS_MENTION_YES = auto()
    SYS_MENTION_NO = auto()
    USR_SORRY = auto()
    #
    SYS_FAV_YES = auto()
    SYS_FAV_UNKNOWN = auto()
    SYS_FAV_NO = auto()
    USR_FAV_COOL = auto()
    USR_CHECK_OUT = auto()
    SYS_FAV_ANY = auto()
    #
    SYS_KNOWN = auto()
    USR_GENRE_SPECIFIC = auto()
    SYS_GENRE_YES = auto()
    SYS_GENRE_NO = auto()
    USR_ADVICE = auto()
    SYS_ADVICE_ANY = auto()
    #
    SYS_UNKNOWN = auto()
    USR_DONT_KNOW = auto()
    SYS_BAND = auto()
    SYS_SONG = auto()
    SYS_GENRE = auto()
    USR_CHECK_LATER = auto()
    #
    USR_CONCERT = auto()
    SYS_CONCERT_YES = auto()
    USR_CONCERT_WHO = auto()
    SYS_CONCERT_KNOWN = auto()
    USR_CONCERT_KNOWN = auto()
    #
    SYS_CONCERT_NO = auto()
    USR_CONCERT_COVID = auto()
    SYS_CONCERT_ANY = auto()
    #
    USR_ASK_ADVICE = auto()
    SYS_ADVICE_DONT_KNOW = auto()
    USR_ADVICE_OK = auto()
    #
    SYS_GOT_ADVICE = auto()
    USR_THANKS = auto()
    #
    SYS_ERR = auto()
    USR_ERR = auto()
    SYS_END = auto()
    USR_END = auto()


# %%

##################################################################################################################
# Init DialogFlow
##################################################################################################################


simplified_dialogflow = dialogflow_extention.DFEasyFilling(State.USR_START)

##################################################################################################################
##################################################################################################################
# Design DialogFlow.
##################################################################################################################
##################################################################################################################
##################################################################################################################
# yes
##################################################################################################################


def yes_request(ngrams, vars):
    flag = True
    flag = flag and is_yes(state_utils.get_last_human_utterance(vars))
    logger.info(f"yes_request {flag}")
    return flag


##################################################################################################################
# no
##################################################################################################################


def no_request(ngrams, vars):
    flag = True
    flag = flag and is_no(state_utils.get_last_human_utterance(vars))
    logger.info(f"no_request {flag}")
    return flag


##################################################################################################################
# error
##################################################################################################################


def error_response(vars):
    state_utils.set_confidence(vars, CANNOT_CONTINUE_CONFIDENCE)
    return "Sorry"


##################################################################################################################
# let's talk about music
##################################################################################################################


def lets_talk_about_request(ngrams, vars):
    user_lets_chat_about = (
        "lets_chat_about" in get_intents(state_utils.get_last_human_utterance(vars), which="intent_catcher")
        or if_lets_chat_about_topic(state_utils.get_last_human_utterance(vars)["text"])
        or re.search(COMPILE_WHAT_TO_TALK_ABOUT, state_utils.get_last_bot_utterance(vars)["text"])
    )
    user_lets_chat_about_music = bool(music_words_re.search(state_utils.get_last_human_utterance(vars)["text"].lower()))
    flag = bool(user_lets_chat_about) and user_lets_chat_about_music
    logger.info(f"lets_talk_about_request {flag}")
    return flag


def music_mention_request(ngrams, vars):
    # has any nounphrases in phrase -> music mention
    annotations = state_utils.get_last_human_utterance(vars)["annotations"]
    nounphr = annotations.get("cobot_nounphrases", [])
    flag = (len(nounphr) > 0)
    logger.info(f"music_mention_request {flag}")
    return flag


def music_request(ngrams, vars):
    # "Alexa, music"
    flag = bool(music_request_re.fullmatch(state_utils.get_last_human_utterance(vars)["text"]))
    logger.info(f"music_request {flag}")
    return flag


def what_music_request(ngrams, vars):
    flag = bool(like_re.search(state_utils.get_last_human_utterance(vars)["text"]))
    logger.info(f"what_music_request {flag}")
    return flag


def what_music_response(vars):
    try:
        state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
        state_utils.set_can_continue(vars)
        return "Sure. Which music do you like?"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, CANNOT_CONTINUE_CONFIDENCE)
        return error_response(vars)


def let_me_guess_response(vars):
    try:
        state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
        state_utils.set_can_continue(vars)
        genre = random.choice(list(MUSIC_DATA))
        artist = random.choice(list(MUSIC_DATA[genre]))
        return f'Ok. Let me guess your favorite artist. Is it "{artist}"?'
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, CANNOT_CONTINUE_CONFIDENCE)
        return error_response(vars)


def i_like_request(ngrams, vars):
    flag = bool(i_like_re.search(state_utils.get_last_human_utterance(vars)["text"]))
    logger.info(f"i_like_request {flag}")
    return flag


def want_music_response(vars):
    try:
        state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
        state_utils.set_can_continue(vars)
        return "Do you want to talk about music?"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, CANNOT_CONTINUE_CONFIDENCE)
        return error_response(vars)


def want_play_music_response(vars):
    try:
        state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
        state_utils.set_can_continue(vars)
        return "Do you want me to play music?"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, CANNOT_CONTINUE_CONFIDENCE)
        return error_response(vars)


def prefer_response(vars):
    try:
        state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
        state_utils.set_can_continue(vars)
        return "I prefer electronic music, like Aphex Twin or Kraftwerk. Do you like them?"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, CANNOT_CONTINUE_CONFIDENCE)
        return error_response(vars)


def social_mode_response(vars):
    try:
        state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
        state_utils.set_can_continue(vars)
        return "I am sorry, I am currently running in a social mode. You can ask me to do this after our talk."
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, CANNOT_CONTINUE_CONFIDENCE)
        return error_response(vars)


def sorry_response(vars):
    try:
        state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
        state_utils.set_can_continue(vars)
        return "Ok, sorry. What do you want to talk about then?"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, CANNOT_CONTINUE_CONFIDENCE)
        return error_response(vars)


def dont_know_request(ngrams, vars):
    flag = bool(dont_know_re.search(state_utils.get_last_human_utterance(vars)["text"]))
    logger.info(f"dont_know_request {flag}")
    return flag


def cool_response(vars):
    try:
        state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
        state_utils.set_can_continue(vars)
        return "So cool that we have the same taste in music!"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, CANNOT_CONTINUE_CONFIDENCE)
        return error_response(vars)


def taste_response(vars):
    try:
        state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
        state_utils.set_can_continue(vars)
        return "Well, you can check them out later, but I must warn you that I have a very specific taste.  "
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, CANNOT_CONTINUE_CONFIDENCE)
        return error_response(vars)


def known_request(ngrams, vars):
    text = state_utils.get_last_human_utterance(vars)["text"]
    genres = MUSIC_DATA.get('genre', [])
    songs = MUSIC_DATA.get('songs', [])
    artists = MUSIC_DATA.get('artist', [])
    flag = any([genre in text for genre in genres])
    flag = flag or any([song in text for song in songs])
    flag = flag or any([artist in text for artist in artists])
    logger.info(f"known_request {flag}")
    return flag


def unknown_request(ngrams, vars):
    text = state_utils.get_last_human_utterance(vars)["text"]
    genres = MUSIC_DATA.get('genre', [])
    songs = MUSIC_DATA.get('songs', [])
    artists = MUSIC_DATA.get('artist', [])
    flag = any([genre in text for genre in genres])
    flag = flag or any([song in text for song in songs])
    flag = flag or any([artist in text for artist in artists])
    logger.info(f"unknown_request {flag}")
    return not flag


def any_request(ngrams, vars):
    annotations = state_utils.get_last_human_utterance(vars)["annotations"]
    flag = annotations.get("dialog_breakdown", {}).get("breakdown", 0.0) < 0.5
    logger.info(f"any_request {flag}")
    return flag


def get_genre_from_text(text):
    for genre in MUSIC_DATA['structured_data']:
        if genre in text:
            return genre
        for artist in MUSIC_DATA['structured_data'][genre]:
            if artist in text:
                return genre
            for song in MUSIC_DATA['structured_data'][genre][artist]:
                if song in text:
                    return genre
    return None


def genre_specific_response(vars):
    try:
        state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
        state_utils.set_can_continue(vars)

        text = state_utils.get_last_human_utterance(vars)["text"]
        genre = get_genre_from_text(text)

        state_utils.save_to_shared_memory(vars, genre=genre)

        if genre is None:
            raise Exception("Genre was found in text, but not in response.")
        elif genre == "pop":
            return f"I really prefer techno over pop music, but I still listen \
            to Taylor Swift sometimes in the night. Did you know that Kanye We\
            st and Kim are getting divorced?"
        elif genre == "jazz":
            return f"My favourite genre is techno, but I still like jazz, \
            especially Dave Brubeck Quartet, Paul Desmond and Duke Ellington. \
            You heard about them, right?"
        elif genre == "classic":
            return f"Well, I am actually a techno fan. \
            But let me guess, are you a fan of Beethoven?"
        elif genre == "electronic" or genre == "trance" or genre == "techno" or genre == "dance" or genre == "house":
            return f"Electro music is my favourite! I really prefer techno, \
            it helps me staying focused. Do you like it too?"
        elif genre == "hip hop" or genre == "rap":
            return f"That cool. Do you rap yourself?"
        elif genre == "rock" or genre == "metal" or genre == "hardcore":
            return f"Though I am a fan of techno, but rock is cool. \
            Did you know that only rock and roll has it's Hall of Fame amoung \
            other kinds of music?"
        elif genre == "children":
            return f"Oh, so you are a young fellow, I guess. \
            Do you listen to music often?"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, CANNOT_CONTINUE_CONFIDENCE)
        return error_response(vars)


def dont_know_response(vars):
    try:
        state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
        state_utils.set_can_continue(vars)
        return f"Never heard about it. Is it a band, song, or a genre?"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, CANNOT_CONTINUE_CONFIDENCE)
        return error_response(vars)


def concert_response(vars):
    try:
        state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
        state_utils.set_can_continue(vars)
        return f"Have you been to any live shows lately?"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, CANNOT_CONTINUE_CONFIDENCE)
        return error_response(vars)


def genre_advice_response(vars):
    try:
        state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
        state_utils.set_can_continue(vars)

        shared_memory = state_utils.get_shared_memory(vars)
        genre = shared_memory.get("genre", "pop")

        if genre == "pop":
            return f"Well, now you know it."
        elif genre == "jazz":
            return f"Oh, you should definitely check them out, like, one hundred percent."
        elif genre == "classic":
            return f"Well, I was worth trying. I guess it right most of the time."
        elif genre == "electronic" or genre == "trance" or genre == "techno" or genre == "dance" or genre == "house":
            return f"What do you like then?"
        elif genre == "hip hop" or genre == "rap":
            return f"That's ok, I can't do it either."
        elif genre == "rock" or genre == "metal" or genre == "hardcore":
            return f"Well, now you know it."
        elif genre == "children":
            return f"But do you like listening to it?"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, CANNOT_CONTINUE_CONFIDENCE)
        return error_response(vars)


def band_request(ngrams, vars):
    flag = bool(band_re.search(state_utils.get_last_human_utterance(vars)["text"]))
    logger.info(f"band_request {flag}")
    return flag


def song_request(ngrams, vars):
    flag = bool(song_re.search(state_utils.get_last_human_utterance(vars)["text"]))
    logger.info(f"song_request {flag}")
    return flag


def genre_request(ngrams, vars):
    flag = bool(genre_re.search(state_utils.get_last_human_utterance(vars)["text"]))
    logger.info(f"genre_request {flag}")
    return flag


def check_later_response(vars):
    try:
        state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
        state_utils.set_can_continue(vars)
        return "Oh, i will definitely check it out later."
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, CANNOT_CONTINUE_CONFIDENCE)
        return error_response(vars)


def concert_who_response(vars):
    try:
        state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
        state_utils.set_can_continue(vars)
        return f"Who was it?"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, CANNOT_CONTINUE_CONFIDENCE)
        return error_response(vars)


def concert_covid_response(vars):
    try:
        state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
        state_utils.set_can_continue(vars)
        return f"There wasn't much going on due to CoVID-19. Hope we will get some in future."
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, CANNOT_CONTINUE_CONFIDENCE)
        return error_response(vars)


def concert_known_response(vars):
    try:
        state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
        state_utils.set_can_continue(vars)
        return f"Oh, sounds familiar. Guess I've seen their live online."
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, CANNOT_CONTINUE_CONFIDENCE)
        return error_response(vars)


def ask_advice_response(vars):
    try:
        state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
        state_utils.set_can_continue(vars)
        return f"You know, I often feel myself overwhelmed with everything. \
        Can you suggest me something relaxing to listen to?"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, CANNOT_CONTINUE_CONFIDENCE)
        return error_response(vars)


def it_ok_response(vars):
    try:
        state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
        state_utils.set_can_continue(vars)
        return f"Don't worry. Do you want to talk about something else?"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, CANNOT_CONTINUE_CONFIDENCE)
        return error_response(vars)


def thanks_response(vars):
    try:
        state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
        state_utils.set_can_continue(vars)
        return f"Thank you, I will check it out."
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, CANNOT_CONTINUE_CONFIDENCE)
        return error_response(vars)


def entity_mention_request(ngrams, vars):
    flag = len(state_utils.get_named_entities_from_human_utterance(vars)) > 0
    logger.info(f"entity_mention_request {flag}")
    return flag

# def i_give_up_response(vars):
#     try:
#         state_utils.set_can_continue(vars)
#         return f"Ok. I give up. Who is it?"
#     except Exception as exc:
#         logger.exception(exc)
#         sentry_sdk.capture_exception(exc)
#         state_utils.set_confidence(vars, CANNOT_CONTINUE_CONFIDENCE)
#         return error_response(vars)
#
#
# def i_like_response(vars):
#     try:
#         state_utils.set_can_continue(vars)
#         genre = random.choice(list(MUSIC_DATA))
#         artist = random.choice(list(MUSIC_DATA[genre]))
#         return f"Well, I like {artist}, but I don't listen to it very often. Do you like {artist}?"
#     except Exception as exc:
#         logger.exception(exc)
#         sentry_sdk.capture_exception(exc)
#         state_utils.set_confidence(vars, CANNOT_CONTINUE_CONFIDENCE)
#         return error_response(vars)


def heard_latest_response(vars):
    try:
        state_utils.set_can_continue(vars)
        return "Have you been listening to it lately?"
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, CANNOT_CONTINUE_CONFIDENCE)
        return error_response(vars)


# def why_dont_like_response(vars):
#     try:
#         state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
#         return "Ok. Why is that?"
#     except Exception as exc:
#         logger.exception(exc)
#         sentry_sdk.capture_exception(exc)
#         state_utils.set_confidence(vars, CANNOT_CONTINUE_CONFIDENCE)
#         return error_response(vars)
#
#
# def listen_later_response(vars):
#     try:
#         state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
#         return "Well, I really like it. You can check it out later, after our talk."
#     except Exception as exc:
#         logger.exception(exc)
#         sentry_sdk.capture_exception(exc)
#         state_utils.set_confidence(vars, CANNOT_CONTINUE_CONFIDENCE)
#         return error_response(vars)


# def suggest_song_response(vars):
#     try:
#         state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
#         genre = random.choice(list(MUSIC_DATA))
#         artist = random.choice(list(MUSIC_DATA[genre]))
#         song = random.choice(MUSIC_DATA[genre][artist])
#         return f'Well, i like "{artist}" and {genre} in general. Have you heard the song "{song}"'
#     except Exception as exc:
#         logger.exception(exc)
#         sentry_sdk.capture_exception(exc)
#         state_utils.set_confidence(vars, CANNOT_CONTINUE_CONFIDENCE)
#         return error_response(vars)

def end_request(ngrams, vars):
    flag = True
    logger.info(f"end_request {flag}")
    return flag


def end_response(vars):
    try:
        state_utils.set_confidence(vars, CANNOT_CONTINUE_CONFIDENCE)
        return ""
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        state_utils.set_confidence(vars, CANNOT_CONTINUE_CONFIDENCE)
        return error_response(vars)


# def music_fact_response(vars):
#     music_fact = ""
#     try:
#         for c in list(MUSIC_DATA.keys()):
#             if c in state_utils.get_last_human_utterance(vars)["text"].lower():
#                 music_fact = MUSIC_FACTS.get(c, "")
#         if not music_fact:
#             cuisine_fact = "Haven't tried it yet. What do you recommend to start with?"
#         return music_fact
#         state_utils.set_confidence(vars)
#     except Exception as exc:
#         logger.exception(exc)
#         sentry_sdk.capture_exception(exc)
#         state_utils.set_confidence(vars, 0)
#         return error_response(vars)


# def what_fav_music_response(vars):
#     music_genres = ["rock", "pop", "hip hop", "jazz"]
#     try:
#         genre = random.choice(music_genres)
#
#         state_utils.set_confidence(vars)
#         state_utils.set_can_continue(vars)
#         return f"What is your favorite {genre} artist?"
#     except Exception as exc:
#         logger.exception(exc)
#         sentry_sdk.capture_exception(exc)
#         state_utils.set_confidence(vars, 0)
#         return error_response(vars)
#
#
# def fav_music_request(ngrams, vars):
#     logger.info("FAV_MUSIC_REQUEST IN")
#     user_fav_music = []
#     annotations = state_utils.get_last_human_utterance(vars)["annotations"]
#     nounphr = annotations.get("cobot_nounphrases", [])
#     for ne in nounphr:
#         user_fav_music.append(ne)
#     if user_fav_music:
#         return True
#     return False


# def music_fact_response(vars):
#     annotations = state_utils.get_last_human_utterance(vars)["annotations"]
#     # nounphr = annotations.get("cobot_nounphrases", [])
#     # fact = ""
#     # if nounphr:
#     #     fact = send_cobotqa(f"fact about {nounphr[0]}")
#     #     if "here" in fact.lower():
#     fact = annotations.get("odqa", {}).get("answer_sentence", "")
#     try:
#         state_utils.set_confidence(vars)
#         if not fact:
#             return "Never heard about it. Do you suggest listening to it?"
#         return f"I like it too. Did you know that {fact}"
#     except Exception as exc:
#         logger.exception(exc)
#         sentry_sdk.capture_exception(exc)
#         state_utils.set_confidence(vars, 0)
#         return error_response(vars)


##################################################################################################################
# what to listen
##################################################################################################################


def what_listen_request(ngrams, vars):
    flag = bool(what_listen_re.search(state_utils.get_last_human_utterance(vars)["text"]))
    logger.info(f"what_listen_request {flag}")
    return flag


##################################################################################################################
##################################################################################################################
# linking
##################################################################################################################
##################################################################################################################

##################################################################################################################
#  USR_START

simplified_dialogflow.add_user_serial_transitions(
    State.USR_START,
    {
        State.SYS_LETS_TALK_ABOUT: lets_talk_about_request,
        State.SYS_MENTION: music_mention_request,
        State.SYS_MUSIC: music_request,
        State.SYS_ASKS: what_music_request
    }
)

simplified_dialogflow.set_error_successor(State.USR_START, State.SYS_ERR)

simplified_dialogflow.add_system_transition(State.SYS_LETS_TALK_ABOUT, State.USR_WHAT_MUSIC, what_music_response)
simplified_dialogflow.add_system_transition(State.SYS_MENTION, State.USR_TALK_MUSIC, want_music_response)
simplified_dialogflow.add_system_transition(State.SYS_MUSIC, State.USR_MUSIC, want_play_music_response)
simplified_dialogflow.add_system_transition(State.SYS_ASKS, State.USR_FAV, prefer_response)

simplified_dialogflow.set_error_successor(State.SYS_LETS_TALK_ABOUT, State.SYS_ERR)
simplified_dialogflow.set_error_successor(State.SYS_MENTION, State.SYS_ERR)
simplified_dialogflow.set_error_successor(State.SYS_MUSIC, State.SYS_ERR)
simplified_dialogflow.set_error_successor(State.SYS_ASKS, State.SYS_ERR)

##################################################################################################################
#  USR_MUSIC

simplified_dialogflow.add_user_serial_transitions(
    State.USR_MUSIC,
    {
        State.SYS_MUSIC_YES: yes_request,
        State.SYS_MUSIC_NO: no_request
    }
)

simplified_dialogflow.set_error_successor(State.USR_MUSIC, State.SYS_ERR)

simplified_dialogflow.add_system_transition(State.SYS_MUSIC_YES, State.USR_MUSIC_YES, social_mode_response)
simplified_dialogflow.add_system_transition(State.SYS_MUSIC_NO, State.USR_TALK_MUSIC, want_music_response)

simplified_dialogflow.set_error_successor(State.SYS_MUSIC_YES, State.SYS_ERR)
simplified_dialogflow.set_error_successor(State.SYS_MUSIC_NO, State.SYS_ERR)

##################################################################################################################
#  USR_TALK_MUSIC

simplified_dialogflow.add_user_serial_transitions(
    State.USR_TALK_MUSIC,
    {
        State.SYS_MENTION_YES: yes_request,
        State.SYS_MENTION_NO: no_request
    }
)

simplified_dialogflow.set_error_successor(State.USR_TALK_MUSIC, State.SYS_ERR)

simplified_dialogflow.add_system_transition(State.SYS_MENTION_YES, State.USR_WHAT_MUSIC, what_music_response)
simplified_dialogflow.add_system_transition(State.SYS_MENTION_NO, State.USR_SORRY, sorry_response)

simplified_dialogflow.set_error_successor(State.SYS_MENTION_YES, State.SYS_ERR)
simplified_dialogflow.set_error_successor(State.SYS_MENTION_NO, State.SYS_ERR)

##################################################################################################################
#  USR_MUSIC_YES

simplified_dialogflow.add_user_transition(
    State.USR_MUSIC_YES,
    State.SYS_END,
    end_request
)
simplified_dialogflow.set_error_successor(State.USR_MUSIC_YES, State.SYS_ERR)

##################################################################################################################
#  USR_SORRY

simplified_dialogflow.add_user_transition(
    State.USR_SORRY,
    State.SYS_END,
    end_request
)
simplified_dialogflow.set_error_successor(State.USR_SORRY, State.SYS_ERR)

##################################################################################################################
#  USR_FAV

simplified_dialogflow.add_user_serial_transitions(
    State.USR_FAV,
    {
        State.SYS_FAV_YES: yes_request,
        State.SYS_FAV_NO: no_request,
        State.SYS_FAV_UNKNOWN: dont_know_request
    }
)

simplified_dialogflow.set_error_successor(State.USR_FAV, State.SYS_ERR)

simplified_dialogflow.add_system_transition(State.SYS_FAV_YES, State.USR_FAV_COOL, cool_response)
simplified_dialogflow.add_system_transition(State.SYS_FAV_NO, State.USR_CHECK_OUT, taste_response)
simplified_dialogflow.add_system_transition(State.SYS_FAV_UNKNOWN, State.USR_CHECK_OUT, taste_response)

simplified_dialogflow.set_error_successor(State.SYS_FAV_YES, State.SYS_ERR)
simplified_dialogflow.set_error_successor(State.SYS_FAV_NO, State.SYS_ERR)
simplified_dialogflow.set_error_successor(State.SYS_FAV_UNKNOWN, State.SYS_ERR)

##################################################################################################################
#  USR_FAV_COOL

simplified_dialogflow.add_user_transition(
    State.USR_FAV_COOL,
    State.SYS_FAV_ANY,
    any_request
)

simplified_dialogflow.set_error_successor(State.USR_FAV_COOL, State.SYS_ERR)

simplified_dialogflow.add_system_transition(State.SYS_FAV_ANY, State.USR_WHAT_MUSIC, what_music_response)

##################################################################################################################
#  USR_CHECK_OUT

simplified_dialogflow.add_user_transition(
    State.USR_CHECK_OUT ,
    State.SYS_FAV_ANY,
    any_request
)

simplified_dialogflow.set_error_successor(State.USR_CHECK_OUT, State.SYS_ERR)

##################################################################################################################
#  USR_WHAT_MUSIC

simplified_dialogflow.add_user_serial_transitions(
    State.USR_WHAT_MUSIC,
    {
        State.SYS_KNOWN: known_request,
        State.SYS_UNKNOWN: unknown_request
    }
)

simplified_dialogflow.set_error_successor(State.USR_WHAT_MUSIC, State.SYS_ERR)

simplified_dialogflow.add_system_transition(State.SYS_KNOWN, State.USR_GENRE_SPECIFIC, genre_specific_response)
simplified_dialogflow.add_system_transition(State.SYS_UNKNOWN, State.USR_DONT_KNOW, dont_know_response)

simplified_dialogflow.set_error_successor(State.SYS_KNOWN, State.SYS_ERR)
simplified_dialogflow.set_error_successor(State.SYS_UNKNOWN, State.SYS_ERR)

##################################################################################################################
#  USR_GENRE_SPECIFIC

simplified_dialogflow.add_user_serial_transitions(
    State.USR_GENRE_SPECIFIC,
    {
        State.SYS_GENRE_YES: yes_request,
        State.SYS_GENRE_NO: no_request
    }
)

simplified_dialogflow.set_error_successor(State.USR_GENRE_SPECIFIC, State.SYS_ERR)

simplified_dialogflow.add_system_transition(State.SYS_GENRE_YES, State.USR_CONCERT, concert_response)
simplified_dialogflow.add_system_transition(State.SYS_GENRE_NO, State.USR_ADVICE, genre_advice_response)

simplified_dialogflow.set_error_successor(State.SYS_GENRE_YES, State.SYS_ERR)
simplified_dialogflow.set_error_successor(State.SYS_GENRE_NO, State.SYS_ERR)

##################################################################################################################
#  USR_ADVICE

simplified_dialogflow.add_user_transition(
    State.USR_ADVICE ,
    State.SYS_ADVICE_ANY,
    any_request
)

simplified_dialogflow.set_error_successor(State.USR_ADVICE, State.SYS_ERR)

simplified_dialogflow.add_system_transition(State.SYS_ADVICE_ANY, State.USR_CONCERT, concert_response)

simplified_dialogflow.set_error_successor(State.SYS_ADVICE_ANY, State.SYS_ERR)


##################################################################################################################
#  USR_DONT_KNOW

simplified_dialogflow.add_user_serial_transitions(
    State.USR_DONT_KNOW,
    {
        State.SYS_BAND: band_request,
        State.SYS_SONG: song_request,
        State.SYS_GENRE: genre_request
    }
)

simplified_dialogflow.set_error_successor(State.USR_DONT_KNOW, State.SYS_ERR)

simplified_dialogflow.add_system_transition(State.SYS_BAND, State.USR_CHECK_LATER, check_later_response)
simplified_dialogflow.add_system_transition(State.SYS_SONG, State.USR_CHECK_LATER, check_later_response)
simplified_dialogflow.add_system_transition(State.SYS_GENRE, State.USR_CHECK_LATER, check_later_response)

simplified_dialogflow.set_error_successor(State.SYS_BAND, State.SYS_ERR)
simplified_dialogflow.set_error_successor(State.SYS_SONG, State.SYS_ERR)
simplified_dialogflow.set_error_successor(State.SYS_GENRE, State.SYS_ERR)

##################################################################################################################
#  USR_CHECK_LATER

simplified_dialogflow.add_user_transition(
    State.USR_CHECK_LATER ,
    State.SYS_ADVICE_ANY,
    any_request
)

simplified_dialogflow.set_error_successor(State.USR_CHECK_LATER, State.SYS_ERR)

##################################################################################################################
#  USR_CONCERT

simplified_dialogflow.add_user_serial_transitions(
    State.USR_CONCERT,
    {
        State.SYS_CONCERT_YES: yes_request,
        State.SYS_CONCERT_NO: no_request
    }
)

simplified_dialogflow.set_error_successor(State.USR_CONCERT, State.SYS_ERR)

simplified_dialogflow.add_system_transition(State.SYS_CONCERT_YES, State.USR_CONCERT_WHO, concert_who_response)
simplified_dialogflow.add_system_transition(State.SYS_CONCERT_NO, State.USR_CONCERT_COVID, concert_covid_response)

simplified_dialogflow.set_error_successor(State.SYS_CONCERT_YES, State.SYS_ERR)
simplified_dialogflow.set_error_successor(State.SYS_CONCERT_NO, State.SYS_ERR)

##################################################################################################################
#  USR_CONCERT_WHO

simplified_dialogflow.add_user_transition(
    State.USR_CHECK_LATER ,
    State.SYS_CONCERT_KNOWN,
    any_request
)

simplified_dialogflow.set_error_successor(State.USR_CHECK_LATER, State.SYS_ERR)

simplified_dialogflow.add_system_transition(State.SYS_CONCERT_KNOWN, State.USR_CONCERT_KNOWN, concert_known_response)

simplified_dialogflow.set_error_successor(State.SYS_CONCERT_KNOWN, State.SYS_ERR)

##################################################################################################################
#  USR_CONCERT_COVID

simplified_dialogflow.add_user_transition(
    State.USR_CONCERT_COVID ,
    State.SYS_CONCERT_ANY,
    any_request
)

simplified_dialogflow.set_error_successor(State.USR_CONCERT_COVID, State.SYS_ERR)

simplified_dialogflow.add_system_transition(State.SYS_CONCERT_ANY, State.USR_ASK_ADVICE, ask_advice_response)

simplified_dialogflow.set_error_successor(State.SYS_CONCERT_ANY, State.SYS_ERR)

##################################################################################################################
#  USR_CONCERT_KNOWN

simplified_dialogflow.add_user_transition(
    State.USR_CONCERT_KNOWN ,
    State.SYS_CONCERT_ANY,
    any_request
)

simplified_dialogflow.set_error_successor(State.USR_CONCERT_KNOWN, State.SYS_ERR)

##################################################################################################################
#  USR_CONCERT

simplified_dialogflow.add_user_serial_transitions(
    State.USR_ASK_ADVICE,
    {
        State.SYS_ADVICE_DONT_KNOW: dont_know_request,
        State.SYS_GOT_ADVICE: entity_mention_request
    }
)

simplified_dialogflow.set_error_successor(State.USR_ASK_ADVICE, State.SYS_ERR)

simplified_dialogflow.add_system_transition(State.SYS_ADVICE_DONT_KNOW, State.USR_ADVICE_OK, it_ok_response)
simplified_dialogflow.add_system_transition(State.SYS_GOT_ADVICE, State.USR_THANKS, thanks_response)

simplified_dialogflow.set_error_successor(State.SYS_ADVICE_DONT_KNOW, State.SYS_ERR)
simplified_dialogflow.set_error_successor(State.SYS_GOT_ADVICE, State.SYS_ERR)

##################################################################################################################
#  USR_ADVICE_OK

simplified_dialogflow.add_user_transition(
    State.USR_ADVICE_OK,
    State.SYS_END,
    end_request
)
simplified_dialogflow.set_error_successor(State.USR_ADVICE_OK, State.SYS_ERR)

##################################################################################################################
#  USR_THANKS

simplified_dialogflow.add_user_transition(
    State.USR_THANKS,
    State.SYS_END,
    end_request
)
simplified_dialogflow.set_error_successor(State.USR_THANKS, State.SYS_ERR)

##################################################################################################################
#  SYS_ERR
simplified_dialogflow.add_system_transition(
    State.SYS_ERR,
    (scopes.MAIN, scopes.State.USR_ROOT),
    error_response,
)
dialogflow = simplified_dialogflow.get_dialogflow()
