import logging
from typing import Callable, List
import datetime
import json
import random

from dff.core import Context, Actor
import dff.conditions as cnd

from common.books import QUESTIONS_ABOUT_BOOKS, SWITCH_BOOK_SKILL_PHRASE
from common.gaming import ALL_LINKS_TO_BOOKS

logger = logging.getLogger(__name__)
# ....

START_PHRASE = "Books are my diamonds. Do you love reading?"
UNCERTAINTY = [" It's not always easy to tell, of course.", " It's only my opinion, though."]
FAVOURITE_BOOK_PHRASES = [
    "Do you want to know what my favourite book is?",
    "Do you want to know what my other favourite book is?",
    "Do you want to hear about one more book that impressed me?",
]
OPINION_REQUEST_ON_BOOK_PHRASES = [
    "Did you enjoy this book?",
    "Did you find this book interesting?",
    "Was this book exciting for you?",
]

READ_BOOK_ADVICES = [
    "You can read it. You won't regret!",
    "You can read this book. You will enjoy it!",
    "I think you will love this book!",
]

DID_NOT_EXIST = ["I didn't exist at that time.", "I'm a bit too young to remember those times though."]

HAVE_YOU_READ_BOOK = "Have you read it?"
ASK_ABOUT_OFFERED_BOOK = "It's a real showpiece. Have you read it?"
TELL_REQUEST = "May I tell you something about this book?"
TELL_REQUEST2 = "Would you like to hear something else about this book?"
WHAT_BOOK_IMPRESSED_MOST = "What book impressed you the most?"
WHEN_IT_WAS_PUBLISHED = "Do you want to know when it was first published?"
WHAT_BOOK_LAST_READ = SWITCH_BOOK_SKILL_PHRASE
BOOK_ANY_PHRASE = "I see you can't name it. Could you please name any book you have read?"
OFFER_FACT_ABOUT_BOOK  = "Would you like to hear a fact about it?"
BOOK_SKILL_QUESTIONS = [WHAT_BOOK_LAST_READ, WHAT_BOOK_IMPRESSED_MOST]
ALL_QUESTIONS_ABOUT_BOOK = QUESTIONS_ABOUT_BOOKS + BOOK_SKILL_QUESTIONS + ALL_LINKS_TO_BOOKS

WHAT_GENRE_FAV = "I have read a plenty of books from different genres. What's the genre that you like?"
ASK_GENRE_OF_BOOK = "Do you know what is the genre of this book?"
GENRE_ADVICE_PHRASE = "By the way, may I advice you a book from this genre?"
GENRE_PHRASES = json.load(open("genre_phrases.json", "r"))[0]
FAVOURITE_GENRE_ANSWERS = list(GENRE_PHRASES.values())

CURRENT_YEAR = datetime.datetime.today().year
FAVOURITE_BOOK_ATTRS = {
    "The Catcher in the Rye": {
        "cur_book_name": "The Catcher in the Rye",
        "cur_book_ago": f"{CURRENT_YEAR - 1951} years ",
        "cur_book_plain": "Q183883", 
        "cur_book_author": "Jerome Salinger",
        "cur_genre": "a novel",
        "fav_book_init": f' My favourite book is "The catcher in the rye" by Jerome David Salinger.',
        "cur_book_about": f'The novel "The catcher in the rye" tells the story of a teenager '
        f"who has been kicked out of a boarding school. "
        f"This is my favourite story, it is truly fascinating."
    },
    "The NeverEnding Story": {
        "cur_book_name": "The NeverEnding Story",
        "cur_book_ago": f"{CURRENT_YEAR - 1979} years ",
        "cur_book_plain": "Q463108", 
        "cur_book_author": "Michael Ende",
        "cur_genre": "a novel",
        "fav_book_init": f'My other favourite book is "The NeverEnding Story" by Michael Ende.',
        "cur_book_about": f' The "NeverEnding Story" tells the story of a troubled young boy Bastien '
        f"who escapes some pursuing bullies in an old book shop. "
        f"While he reads the book, he suddenly moves into the world described there, "
        f"as the only one who can save it."        
    },
    "The Little Prince": {
        "cur_book_name": "The Little Prince",
        "cur_book_ago": f"{CURRENT_YEAR - 1943} years ",
        "cur_book_plain": "Q25338", 
        "cur_book_author": "Antoine de Saint-Exupéry",
        "cur_genre": "a novel",
        "fav_book_init": f'I was really impressed by the book "The Little Prince" ' f"by Antoine de Saint-Exupéry.",
        "cur_book_about": f" The Little Prince is a poetic tale, with watercolor illustrations by the author, "
        f"in which a pilot stranded in the desert meets a young prince "
        f"visiting Earth from a tiny asteroid."        
    },    
}

def append_unused(
    initial:str,
    phrases: List[str], 
    exit_on_exhaust: bool=False
) -> Callable:
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

        target_idx = confidences.index(max(confidences))
        target_phrase = phrases[target_idx]
        used.append(id(target_phrase))
        ctx.misc["used_phrases"] = used

        if exit_on_exhaust:
            label = ctx.last_label
            actor.plot[label[0]][label[1]].transitions = {
                ("global_flow", "fallback", 2): cnd.true()
            }
            return initial
        return initial + target_phrase
    
    return unused_handler

def genre_phrase(ctx: Context, actor: Actor):
    genre = ctx.misc.get("slots", {}).get("cur_genre", "fiction")
    response = append_unused("", GENRE_PHRASES[genre], exit_on_exhaust=True)(ctx, actor)
    response = append_unused(f"{response} ", [GENRE_ADVICE_PHRASE])(ctx, actor)
    return response


def append_question(initial: str, additional=None) -> Callable:
    def question_handler(ctx: Context, actor: Actor) -> str:
        """
        Implements the original booklink2reply intended to change the branch
        Exits the skill if no questions remain
        """
        questions: List[str] = [] if not additional else [additional]
        used = ctx.misc.get("used_phrases", [])
        if not id(WHAT_BOOK_IMPRESSED_MOST) in used:
            questions.append(WHAT_BOOK_IMPRESSED_MOST)
        
        first_fav_named = id(FAVOURITE_BOOK_PHRASES[0]) in used
        if not first_fav_named:
            questions.append(FAVOURITE_BOOK_PHRASES[0])

        second_fav_named = any([id(x) in used for x in FAVOURITE_BOOK_PHRASES[1:]])
        if first_fav_named and not second_fav_named:
            questions.extend(FAVOURITE_BOOK_PHRASES[1:])

        if not ctx.misc.get("flags", {}).get("user_fav_genre_visited", False):
            questions.append(WHAT_GENRE_FAV)
        random.shuffle(questions)
        return append_unused(initial, questions, exit_on_exhaust=True)(ctx, actor)
    
    return question_handler