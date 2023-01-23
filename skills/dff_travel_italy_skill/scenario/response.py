import logging
from typing import Callable, List
import datetime
import json
import random

from df_engine.core import Context, Actor
import df_engine.conditions as cnd

import common.travel as templates
from common.travel_italy import SWITCH_ITALY_TRAVEL_SKILL_PHRASE, QUESTIONS_ABOUT_ITALY


logger = logging.getLogger(__name__)
# ....

START_PHRASE = "Italy is my paradise. Do you love this country?"
UNCERTAINTY = [
    " It's not always easy to tell, of course.",
    " It's only my opinion, though.",
]
FAVOURITE_PLACE_PHRASES = [
    "Do you want to know what my favourite place in Italy is?",
    "Do you want to know what my other favourite place in Italy is?",
    "Do you want to hear about one more place in Italy that impressed me?",
]
OPINION_REQUEST_ON_ITALY_PHRASES = [
    "Did you enjoy going to Italy?",
    "Did you find this place interesting?",
    "Was the trip to Italy exciting for you?",
]

VISIT_PLACE_ADVICES = [
    "You should go there one day. You won't regret it!",
    "You should put it on your bucket list!",
    "I think you would love this place!",
]

DID_NOT_EXIST = [
    "I didn't exist at that time.",
    "I'm a bit too young to remember those times though.",
]

WHAT_DID_DAY = "What did you do during the day?" 

HAVE_YOU_BEEN_PLACE = "Have you been there?"
ASK_ABOUT_OFFERED_LOC = "It's a real wonder. Have you been there?"
TELL_REQUEST = "May I tell you something about this place?"
TELL_REQUEST2 = "Would you like to hear something else about this place?"
WHAT_PLACE_IMPRESSED_MOST = "What place impressed you the most?"
WHAT_PLACE_LAST_VISITED = "What place in Italy did you last visit?"
OFFER_FACT_ABOUT_PLACE = "Would you like to hear a fact about it?"
ITALY_TRAVEL_SKILL_QUESTIONS = [WHAT_PLACE_LAST_VISITED, WHAT_PLACE_IMPRESSED_MOST]
ALL_QUESTIONS_ABOUT_ITALY = QUESTIONS_ABOUT_ITALY + ITALY_TRAVEL_SKILL_QUESTIONS
WHO_TRAVEL_WITH = "Who did you go there with?"
WHEN_TRAVEL = "When did you go there?"

# WHAT_GENRE_FAV = "I have read a plenty of books from different genres. What's the genre that you like?"
# ASK_GENRE_OF_BOOK = "Do you know what is the genre of this book?"
# GENRE_ADVICE_PHRASE = "By the way, may I advice you a book from this genre?"
# GENRE_PHRASES = json.load(open("genre_phrases.json", "r"))[0]
# FAVOURITE_GENRE_ANSWERS = list(GENRE_PHRASES.values())

CURRENT_YEAR = datetime.datetime.today().year
# FAVOURITE_BOOK_ATTRS = {
#     "The Catcher in the Rye": {
#         "cur_book_name": "The Catcher in the Rye",
#         "cur_book_ago": f"{CURRENT_YEAR - 1951} years ",
#         "cur_book_plain": "Q183883",
#         "cur_book_author": "Jerome Salinger",
#         "cur_genre": "a novel",
#         "fav_book_init": ' My favourite book is "The catcher in the rye" by Jerome David Salinger.',
#         "cur_book_about": 'The novel "The catcher in the rye" tells the story of a teenager '
#         "who has been kicked out of a boarding school. "
#         "This is my favourite story, it is truly fascinating.",
#     },
#     "The NeverEnding Story": {
#         "cur_book_name": "The NeverEnding Story",
#         "cur_book_ago": f"{CURRENT_YEAR - 1979} years ",
#         "cur_book_plain": "Q463108",
#         "cur_book_author": "Michael Ende",
#         "cur_genre": "a novel",
#         "fav_book_init": 'My other favourite book is "The NeverEnding Story" by Michael Ende.',
#         "cur_book_about": ' The "NeverEnding Story" tells the story of a troubled young boy Bastien '
#         "who escapes some pursuing bullies in an old book shop. "
#         "While he reads the book, he suddenly moves into the world described there, "
#         "as the only one who can save it.",
#     },
#     "The Little Prince": {
#         "cur_book_name": "The Little Prince",
#         "cur_book_ago": f"{CURRENT_YEAR - 1943} years ",
#         "cur_book_plain": "Q25338",
#         "cur_book_author": "Antoine de Saint-Exupéry",
#         "cur_genre": "a novel",
#         "fav_book_init": 'I was really impressed by the book "The Little Prince" ' "by Antoine de Saint-Exupéry.",
#         "cur_book_about": " The Little Prince is a poetic tale, with watercolor illustrations by the author, "
#         "in which a pilot stranded in the desert meets a young prince "
#         "visiting Earth from a tiny asteroid.",
#     },
# }


def append_unused(initial: str, phrases: List[str], exit_on_exhaust: bool = False) -> Callable:
    """
    Return an unused or a least used response from a list of options
    """

    def unused_handler(ctx: Context, actor: Actor) -> str:

        used = ctx.misc.get("used_phrases", [])
        confidences = [1] * len(phrases)

        for idx, phrase in enumerate(phrases):
            times: int = used.count(id(phrase))
            if times == 0:
                used.append(id(phrase))
                ctx.misc["used_phrases"] = used
                return initial + phrase
            confidences[idx] *= 0.4 ** times

        if exit_on_exhaust:
            label = ctx.last_label
            actor.plot[label[0]][label[1]].transitions = {("global_flow", "fallback", 2): cnd.true()}
            return initial

        target_idx = confidences.index(max(confidences))
        target_phrase = phrases[target_idx]
        used.append(id(target_phrase))
        ctx.misc["used_phrases"] = used
        return initial + target_phrase

    return unused_handler

