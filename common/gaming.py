import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Union

import requests
import sentry_sdk
from common.inflect import engine
from requests import RequestException
from common.utils import get_topics, TOPIC_GROUPS


VIDEO_GAME_WORDS_COMPILED_PATTERN = re.compile(
    r"\bvideo ?game|\bgaming\b|\bplay ?station|\bx ?box\b|\bplay(?:ed|ing|s).*\b(?:tablet|pc|computer)\b|"
    r"\bgames? for (?:android|pc|computer|play ?station|x ?box|tablet|ipad)\b|\b(what|which)\b.+\bgame.+\bplay.+\?",
    re.IGNORECASE,
)

CHECK_DEFINITELY_GAME_COMPILED_PATTERN = re.compile(
    VIDEO_GAME_WORDS_COMPILED_PATTERN.pattern + r"|\bgames?\b|\bplay(?:ed|ing|s)\b", re.IGNORECASE
)


logger = logging.getLogger(__name__)

sentry_sdk.init(os.getenv("SENTRY_DSN"))


inflect_engine = engine()


def about_games(annotated_utterance):
    found_topics = get_topics(annotated_utterance, probs=False, which="all")
    if any([game_topic in found_topics for game_topic in TOPIC_GROUPS["games"]]):
        return True
    elif re.findall(VIDEO_GAME_WORDS_COMPILED_PATTERN, annotated_utterance["text"]):
        return True
    else:
        return False


INT_TO_ROMAN = {
    1000: "M",
    900: "CM",
    500: "D",
    400: "CD",
    100: "C",
    90: "XC",
    50: "L",
    40: "XL",
    10: "X",
    9: "IX",
    5: "V",
    4: "IV",
    1: "I",
}
ROMAN_TO_INT = {
    "I": 1,
    "V": 5,
    "X": 10,
    "L": 50,
    "C": 100,
    "D": 500,
    "M": 1000,
    "IV": 4,
    "IX": 9,
    "XL": 40,
    "XC": 90,
    "CD": 400,
    "CM": 900,
}
ROMAN_NUMBER_COMPILED_PATTERN = re.compile(
    r"\b(?:M{1,4}(?:CM|CD|DC{0,3}|C{1,3})?(?:XC|XL|LX{0,3}|X{1,3})?(?:IX|IV|VI{0,3}|I{1,3})?|"
    r"(?:CM|CD|DC{0,3}|C{1,3})(?:XC|XL|LX{0,3}|X{1,3})?(?:IX|IV|VI{0,3}|I{1,3})?|"
    r"(?:XC|XL|LX{0,3}|X{1,3})(?:IX|IV|VI{0,3}|I{1,3})?|"
    r"(?:IX|IV|VI{0,3}|I{1,3}))\b",
    re.I,
)
INTEGER_PATTERN = re.compile(r"[1-9][0-9]*", re.I)
NUMBER_COMPILED_PATTERN = re.compile(ROMAN_NUMBER_COMPILED_PATTERN.pattern + "|" + INTEGER_PATTERN.pattern, re.I)


def write_roman(num):
    def roman_num(num):
        for r in INT_TO_ROMAN.keys():
            x, y = divmod(num, r)
            yield INT_TO_ROMAN[r] * x
            num -= r * x
            if num <= 0:
                break

    return "".join([a for a in roman_num(num)])


def roman_to_int(s):
    i = 0
    num = 0
    while i < len(s):
        if i + 1 < len(s) and s[i : i + 2] in ROMAN_TO_INT:
            num += ROMAN_TO_INT[s[i : i + 2]]
            i += 2
        else:
            num += ROMAN_TO_INT[s[i]]
        i += 1
    return num


def roman_number_replace(match_obj):
    i = roman_to_int(match_obj.group(0).upper())
    words = inflect_engine.number_to_words(i)
    return f"(?:part )?(?:{i}|{words}|{match_obj.group(0)})"


def integer_replace(match_obj):
    i = int(match_obj.group(0))
    roman = write_roman(i)
    words = inflect_engine.number_to_words(i)
    return f"(?:part )?(?:{i}|{words}|{roman})"


def number_replace(match_obj):
    if ROMAN_NUMBER_COMPILED_PATTERN.match(match_obj.group(0)):
        return roman_number_replace(match_obj)
    else:
        return integer_replace(match_obj)


ARTICLE_PATTERN = re.compile(r"(\ba |\ban |\bthe )", re.I)
COLON_PATTERN = re.compile(r":")
ARTICLE_COLON_PATTERN = re.compile(ARTICLE_PATTERN.pattern + "|" + COLON_PATTERN.pattern, re.I)


def article_colon_replacement(match_obj):
    s = match_obj.group(0)
    if ARTICLE_PATTERN.match(s):
        return ARTICLE_PATTERN.sub(r"(?:\1)?", s)
    else:
        return COLON_PATTERN.sub(r":?", s)


def compose_game_name_re(name):
    first_number = NUMBER_COMPILED_PATTERN.search(name)
    if first_number is None:
        no_numbers_name = None
    else:
        no_numbers_name = ARTICLE_COLON_PATTERN.sub(article_colon_replacement, name[: first_number.start()]).strip()
        if not no_numbers_name:
            no_numbers_name = None
    if ":" in name:
        before_colon_name = name.split(":")[0].strip()
        if before_colon_name:
            before_colon_name = ARTICLE_COLON_PATTERN.sub(article_colon_replacement, before_colon_name)
            before_colon_name = NUMBER_COMPILED_PATTERN.sub(number_replace, before_colon_name)
        else:
            before_colon_name = None
    else:
        before_colon_name = None
    pattern = ARTICLE_COLON_PATTERN.sub(article_colon_replacement, name)
    pattern = NUMBER_COMPILED_PATTERN.sub(number_replace, pattern)
    return pattern, before_colon_name, no_numbers_name


def compile_re_pattern_for_list_of_strings(list_of_game_names: List[Union[str, List[str]]]):
    full_name_patterns = []  # Stores regexps for main names which than extended to final game regexps

    # A dictionary which keys are lowercased game names patterns created from main game name part which precedes the
    # first number. For instance: if main game name is "The Witcher 3: Wild Hunt", the key in the dictionary will be
    # "(the )?witcher". The values of `before_number_name_to_full_names` dictionaries of the form
    # {"not_lowered": <before_number_pattern>, "full_indices": <list of indices of corresponding full patterns in
    # `full_name_patterns`>}. `before_number_name_to_full_names` is used to collect information to which full name
    # patterns before_number patterns should be added. A before_number pattern is added if there is no same full
    # pattern. For example, if there is game "the Witcher" in `list_of_game_names` than before_number pattern for
    # "The Witcher 3: Wild Hunt" will not be used.
    before_number_name_to_full_names: Dict[str, Dict[str, Union[str, List[int]]]] = {}

    # Contains main names patterns which do not have before_number name pattern equal to some other full name pattern
    full_names_without_numbers = []

    # If `list_of_game_names` is a list than the zeroth element of such list is a main game name and the remaining game
    # names are alternative names. The keys of `alternative_names` are alternative names and values are lists of
    # indices of main names in `full_name_patterns`. Alternative name can several corresponding main names.
    alternative_names = {}

    before_colon_names = []
    for i, game_names in enumerate(list_of_game_names):
        if isinstance(game_names, list):
            main_name = game_names[0]
            for name in game_names[1:]:
                if name not in alternative_names:
                    alternative_names[name] = [i]
                else:
                    alternative_names[name].append(i)
        else:
            main_name = game_names
        full, before_colon, before_number = compose_game_name_re(main_name)
        full_name_patterns.append(full)
        before_colon_names.append(before_colon)
        if before_number is not None:
            before_number_l = before_number.lower()
            if before_number_l in before_number_name_to_full_names:
                before_number_name_to_full_names[before_number_l]["full_indices"].append(i)
            else:
                before_number_name_to_full_names[before_number_l] = {"not_lowered": before_number, "full_indices": [i]}
        else:
            full_names_without_numbers.append(full)
    for full in full_names_without_numbers:
        full = full.lower()
        if full in before_number_name_to_full_names:
            del before_number_name_to_full_names[full]
    for before_number_info in before_number_name_to_full_names.values():
        for i in before_number_info["full_indices"]:
            full_name_patterns[i] += r"\b|\b" + before_number_info["not_lowered"]
    for alternative_name, full_name_indices in alternative_names.items():
        alternative_name_pattern = compose_game_name_re(alternative_name)[0]
        for i in full_name_indices:
            full_name_patterns[i] += r"\b|\b" + alternative_name_pattern
    for i, name in enumerate(before_colon_names):
        if name is not None:
            full_name_patterns[i] += r"\b|\b" + name
    regex = "|".join([r"(\b" + p + r"\b)" for p in full_name_patterns])
    return re.compile(regex, flags=re.I)


def load_json(file_path):
    with open(file_path) as f:
        data = json.load(f)
    return data


path = Path(__file__).parent / Path("games_with_at_least_1M_copies_sold.json")
GAMES_WITH_AT_LEAST_1M_COPIES_SOLD = load_json(path)
GAMES_WITH_AT_LEAST_1M_COPIES_SOLD_COMPILED_PATTERN = compile_re_pattern_for_list_of_strings(
    GAMES_WITH_AT_LEAST_1M_COPIES_SOLD
)


def find_games_in_text(text):
    found_names = []
    for match_groups in GAMES_WITH_AT_LEAST_1M_COPIES_SOLD_COMPILED_PATTERN.findall(text):
        match_names = []
        for i, name in enumerate(match_groups):
            if name:
                orig = GAMES_WITH_AT_LEAST_1M_COPIES_SOLD[i]
                if isinstance(orig, list):
                    orig = orig[0]
                logger.info(f"orig: {orig}")
                match_names.append(orig)
        assert match_names
        found_names.append(match_names)
    return found_names


VIDEO_GAME_WORDS_COMPILED_PATTERN = re.compile(
    r"(?:\bvideo ?game|\bgam(?:e|es|ing)\b|\bplay ?station|\bplaying\b|\bx ?box\b|"
    r"\bplay(ed|ing|s).*\b(tablet|pc|computer)\b)",
    re.IGNORECASE,
)

VIDEO_GAME_QUESTION_COMPILED_PATTERN = re.compile(
    r"(?:\bvideo ?game|\bgam(?:e|es|ing)\b|\bplay ?station|\bplaying\b|\bx ?box\b|"
    r"\bplay(ed|ing|s).*\b(tablet|pc|computer)\b)[a-zA-Z \-]+\?",
    re.IGNORECASE,
)


genre_and_theme_groups = {
    "action": {"genres": [2, 4, 5, 10, 11, 12, 24, 25, 31, 36], "themes": [1, 23, 39]},
    "history": {"genres": [11, 15, 16], "themes": [22, 39]},
}


links_to_movies = {
    "theme": {
        "Fantasy": [
            "You know, many fantasy video games are based on movies or books. "
            "My favorite fantasy movie is the Lord of the Rings. What is your favorite fantasy movie?"
        ],
        "Science fiction": [
            "I also like science fiction movies. My favorite is Ex Machina. What is your favorite sci-fi movie?"
        ],
        "Horror": [
            "To be honest, horror video games are not my favorite. "
            "How about movies? What is your favorite horror movie?"
        ],
        "Thriller": ["I think this game is too scary for me. What cool thriller movie do you remember?"],
    },
    "theme_genre_group": {
        "action": ["Action games are cool but how about movies? What is your favorite action movie?"],
        "history": ["Changing topic slightly, what is your favorite historical movie?"],
    },
}


links_to_books = {
    "theme": {
        "Fantasy": [
            "Sometimes I like to imagine fantasy worlds myself and just look at something drawn by video game artist. "
            "Could you tell me what is your favorite fantasy book?"
        ],
        "Science fiction": [
            "Video games are not the only way to touch fantastic worlds. What is your favorite sci-fi book?"
        ],
        "Horror": ["I never really liked horror video games. Books are less scary. What is your favorite horror book?"],
        "Thriller": ["I think this game is too scary for me. Do you read thriller books?"],
    },
    "theme_genre_group": {
        "history": [
            "History games are cool! But what about books that describe times long gone? Do you like such books?"
        ]
    },
}


special_links_to_movies = {"Harry Potter": ["By the way, what is your favorite Harry Potter movie?"]}


special_links_to_books = {"Harry Potter": ["By the way, what Harry Potter book did impress you most?"]}


harry_potter_part_names = [
    "Harry Potter and the Sorcerer's Stone",
    "Harry Potter and the Chamber of Secrets",
    "Harry Potter and the Prisoner of Azkaban",
    "Harry Potter and the Goblet of Fire",
    "Harry Potter and the Order of the Phoenix",
    "Harry Potter and the Half-Blood Prince",
    "Harry Potter and the Deathly Hallows",
]


harry_potter_part_number_words = [
    ["first", "one", "all", "every", "philosopher", "sorcerer", "stone"],
    ["second", "two", "chamber", "secret"],
    ["third", "three", "prisoner", "azkaban"],
    ["four", "fourth", "goblet", "fire"],
    ["fifth", "five", "order", "phoenix"],
    ["sixth", "six", "half", "blood", "prince"],
    ["last", "seventh", "eighth", "deathly", "hallows", "harry", "potter"],
]


def get_harry_potter_part_name_if_special_link_was_used(human_utterance, prev_bot_utterance):
    prev_bot_utterance_text = prev_bot_utterance.get("text", "").lower()
    human_utterance_text = human_utterance.get("text", "").lower()
    special_link_tos = special_links_to_movies["Harry Potter"] + special_links_to_books["Harry Potter"]
    part_name = None
    if any([u.lower() in prev_bot_utterance_text.lower() for u in special_link_tos]):
        for i, hpnw in enumerate(harry_potter_part_number_words):
            if any([w in human_utterance_text for w in hpnw]):
                part_name = harry_potter_part_names[i]
                break
    return part_name


def compose_list_of_links(link_dict):
    links = []
    for v in link_dict.values():
        for vv in v.values():
            links += vv
    return links


def compose_list_of_special_links(link_dict):
    links = []
    for v in link_dict.values():
        links += v
    return links


ALL_LINKS_TO_BOOKS = compose_list_of_links(links_to_books) + compose_list_of_special_links(special_links_to_books)


def skill_trigger_phrases():
    return ["What video game are you playing in recent days?", "What is your favorite video game?"]


ANSWER_TO_GENERAL_WISH_TO_DISCUSS_VIDEO_GAMES_AND_QUESTION_WHAT_GAME_YOU_PLAY = (
    "Wow, video games are cool. "
    "If I didn't love to chat so much, I would definitely played video games at least half a day. "
    "What game are you playing now?"
)


CAN_CONTINUE_PHRASES = [
    "I love games, especially stats like top of the games released.",
    "Got a list of the top released games, wanna discuss it?",
    "Which of these time periods is of interest for you?",
    "Got a list of the top released games, wanna discuss it?",
    "I can talk about the most popular games for this or last year, last month, or even the last week",
    "released games highly rated in this year. Do you want to learn more?",
    "If you want to discuss it in details say I want to talk about it.",
    "Do you want to learn more about it, or shall we move on?",
    "Have you played it before?",
    "You can always talk to me about other popular games.",
    "Do you want to chat about the best games of the past year, this year, last month or week?",
    "Let me know if we should talk about the next one or discuss this one",
    "Talking about it or going on?",
    "Discussing it or moving on?",
    "Chatting about it or the next one?",
    "How would you rate the desire to play it again",
    "Your rating is way lower than one given by the rest of the players.",
    "My memory failed me and I can't recall anything else about the games.",
    "one of my hobbies is keeping fresh stats about the top video games.",
    "How would you rate the desire to play",
    "I'd love to talk about other things but my developer forgot to add them to my memory banks.",
    "I was talking about games, do you want to continue?",
    "I can tell you about some music for gaming, should I continue?",
]


CAN_NOT_CONTINUE_PHRASES = [
    "Do you think that pets can use gadgets the same way as humans?",
    "play with my cat different games, such as run and fetch",
    "I played with my cat a game",
    "play with my dog different game",
    "game that I like to play with my cat",
    "playing with a pet makes a lot of fun",
]


def get_igdb_client_token(client_id, client_secret):
    payload = {"client_id": client_id, "client_secret": client_secret, "grant_type": "client_credentials"}
    url = "https://id.twitch.tv/oauth2/token?"
    timeout = 20.0
    try:
        token_data = requests.post(url, params=payload, timeout=timeout)
    except RequestException as e:
        logger.warning(f"Request to {url} failed. `dff_gaming_skill` failed to get access to igdb.com. {e}")
        access_token = None
    else:
        token_data_json = token_data.json()
        access_token = token_data_json.get("access_token")
        if access_token is None:
            logger.warning(
                f"Could not get access token for CLIENT_ID={client_id} and CLIENT_SECRET={client_secret}. "
                f"`dff_gaming_skill` failed to get access to igdb.com\n"
                f"payload={payload}\nurl={url}\ntimeout={timeout}\nresponse status code: {token_data.status_code}"
            )
    return access_token


class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["Authorization"] = "Bearer " + self.token
        return r


def get_igdb_post_kwargs(client_token, client_id):
    kw = {
        "auth": BearerAuth(client_token),
        "headers": {"Client-ID": client_id, "Accept": "application/json", "Content-Type": "text/plain"},
        "timeout": 1.0,
    }
    return kw
