import json
import re
from pathlib import Path


VIDEO_GAME_WORDS_COMPILED_PATTERN = re.compile(
    r"(?:\bvideo ?game|\bgam(?:e|es|ing)\b|\bplay ?station|\bplaying\b|\bx ?box\b|"
    r"\bplay(ed|ing|s).*\b(tablet|pc|computer)\b)",
    re.IGNORECASE)


def compile_re_pattern_for_list_of_strings(strings):
    regex = r'\b' + r'\b|\b'.join(strings) + r'\b'
    return re.compile(regex, flags=re.I)


def load_json(file_path):
    with open(file_path) as f:
        data = json.load(f)
    return data


GAMES_WITH_AT_LEAST_1M_COPIES_SOLD = load_json(
    Path(__file__).parent / Path("games_with_at_least_1M_copies_sold.json"))
GAMES_WITH_AT_LEAST_1M_COPIES_SOLD_COMPILED_PATTERN = compile_re_pattern_for_list_of_strings(
    GAMES_WITH_AT_LEAST_1M_COPIES_SOLD)


genre_and_theme_groups = {
    "action": {
        "genres": [2, 4, 5, 10, 11, 12, 24, 25, 31, 36],
        "themes": [1, 23, 39]
    },
    "history": {
        "genres": [11, 15, 16],
        "themes": [22, 39]
    }
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
        "Thriller": [
            "I think this game is too scary for me. What cool thriller movie do you remember?"
        ]
    },
    "theme_genre_group": {
        "action": [
            "Action games are cool but how about movies? What is your favorite action movie?"
        ],
        "history": [
            "Changing topic slightly, what is your favorite historical movie?"
        ]
    }
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
        "Horror": [
            "I never really liked horror video games. Books are less scary. What is your favorite horror book?"
        ],
        "Thriller": [
            "I think this game is too scary for me. Do you read thriller books?"
        ]
    },
    "theme_genre_group": {
        "history": [
            "History games are cool! But what about books that describe times long gone? Do you like such books?"
        ]
    }
}


special_links_to_movies = {
    "Harry Potter": ["By the way, what is your favorite Harry Potter movie?"]
}


special_links_to_books = {
    "Harry Potter": ["By the way, what Harry Potter book did impress you most?"]
}


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
