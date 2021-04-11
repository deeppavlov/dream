import re
from random import choice

from common.utils import get_entities

MOVIE_SKILL_CHECK_PHRASE = "the recent movie"
SWITCH_MOVIE_SKILL_PHRASE = f"What is {MOVIE_SKILL_CHECK_PHRASE} you've watched?"

MOVIE_COMPILED_PATTERN = re.compile(
    r"(movie|film|picture|series|tv[ -]?show|reality[ -]?show|netflix|\btv\b|"
    r"comedy|comedies|thriller|animation|anime|talk[ -]?show|cartoon|drama|"
    r"fantasy)", re.IGNORECASE)


def skill_trigger_phrases():
    return [SWITCH_MOVIE_SKILL_PHRASE] + ABOUT_MOVIE_TITLES_PHRASES


def movie_skill_was_proposed(prev_bot_utt):
    return MOVIE_SKILL_CHECK_PHRASE in prev_bot_utt.get('text', '').lower()


ABOUT_MOVIE_TITLES_PHRASES = [
    "What is your all-time favorite movie?",
    # "What is your favorite movie?",
    "What is the best movie you have ever seen?",
    "What is the scariest movie you have ever seen?",
    "What is the funniest movie you have ever seen?",
    "What is the most romantic movie you have ever seen?",
    "What movie you could watch over and over again?",
    # "Have you seen any good movies lately?",
    # "What was the last movie you watched?",
    "What is your favorite TV-series?",
    # "What is your favorite TV-show?",
    # "What was the last TV-series you watched?",
]
ABOUT_MOVIE_PERSONS_PHRASES = [
    "What movie star would you most like to meet?",
    "Who is your favorite actor or actress?",
    "Who is your favorite director?",
    "Which famous person would you like to have for a best friend?",

]

ALL_PHRASES_FOR_MOVIE_SKILL = ABOUT_MOVIE_TITLES_PHRASES + ABOUT_MOVIE_PERSONS_PHRASES


def get_movie_template(category, subcategory=None, movie_type="movie"):
    templates = {
        "never_heard_about_template": [
            "I've never heard about SUBJECT before.",
            "I've never heard about SUBJECT previously."],
        "opinion_request_about_movie": [
            "What do you think about it?",
            "What is your view on it?",
            "What is your opinion on it?"],
        "heard_about_template": [
            "Yeah, I've heard about SUBJECT,",
            "Yeah, I know SUBJECT,",
            "I've got what you are talking about."],
        "clarification_template": [
            "Did I get correctly that you are talking about",
            "Am I right in thinking that you are talking about",
            "Did I get correctly that you meant",
            "Am I right in thinking that you meant"],
        "sorry_didnt_get_title": [
            "Sorry, I could not get what TYPE you are talking about,",
            "Sorry, I didn't get what TYPE you meant"],
        "lets_talk_about_other_movie": [
            "Let's talk about some other movie.",
            "Maybe you want to talk about some other movie.",
            "Do you want to discuss some other movie."],
        "user_opinion_comment": {
            "positive": ['Cool!', "Great!", "Nice!"],
            "neutral": ["Okay.", "Well.", "Hmm.."],
            "negative": ["I see.", "That's okay.", "Okay."]},
        "didnt_get_movie_title_at_all": [
            "Sorry, I didn't get the title, could you, please, repeat it.",
            "Sorry, I didn't understand the title, could you, please, repeat it.",
            "Sorry, I didn't catch the title, could you, please, repeat it.",
            "Sorry, I didn't get the title, can you, please, repeat it."],
        "dont_know_movie_title_at_all": [
            "Sorry, probably I've never heard about this TYPE,",
            "Sorry, maybe I just have never heard about this TYPE,",
            "Well, probably I've never heard about this TYPE,"],
        "lets_move_on": [
            "Let's move on.",
            "Okay.",
            "Hmmm.",
            "Huh.",
            "Aha.",
            ""]
    }
    if subcategory is not None:
        return choice(templates[category].get(subcategory, "")).replace(
            "TYPE", movie_type).replace("SUBJECT", choice(["it", f"this {movie_type}"]))
    else:
        return choice(templates[category]).replace(
            "TYPE", movie_type).replace("SUBJECT", choice(["it", f"this {movie_type}"]))


def extract_movies_names_from_annotations(annotated_uttr):
    if "cobot_entities" in annotated_uttr["annotations"]:
        movies_titles = []
        entities = get_entities(annotated_uttr, only_named=False, with_labels=True)
        for ent in entities:
            if ent.get("label", "") == "videoname":
                movies_titles += [ent["text"]]
    else:
        movies_titles = None
    return movies_titles
