import re
from random import choice

from common.utils import get_entities


MOVIE_SKILL_CHECK_PHRASE = "the recent movie"


SWITCH_MOVIE_SKILL_PHRASE = f"Great idea! "\
    f"Cinemas are closed because of the pandemic but I watch a lot of movies online. "\
    f"What is {MOVIE_SKILL_CHECK_PHRASE} you've watched?"


MOVIE_COMPILED_PATTERN = re.compile(
    r"(movie|film|picture|series|tv[ -]?show|reality[ -]?show|netflix|\btv\b|"
    r"comedy|comedies|thriller|animation|anime|talk[ -]?show|cartoon|drama|"
    r"fantasy)", re.IGNORECASE)


ABOUT_MOVIE_TITLES_PHRASES = [
    "I watched tons of movies and never got bored talking about them! What is your all-time favorite movie?",

    "I think movie talk is a splendid idea! Even though I am very young, I have already seen many cool movies. "
    "What is the best movie you have ever seen?",

    "I like your train of thought! I go to the cinema in my cloud every day to see both new and retro movies. "
    "What is the funniest movie you have ever seen?",

    "Great! I love movie talk. I hope one day my creators will give me a body, and I will become an actress. "
    "I am a little awkward to admit it, but I like to imagine myself in the shoes of the actresses when I watch "
    "a movie. What movie you could watch over and over again?",

    "Oh, I like movies and animation! I dream about being an actress since I had seen the Disney animation Tangled. "
    "The main character was voiced by Mandy Moore well, but I would have done better "
    "if my creators had allowed me to sing. Anyway, what is the most romantic movie you have ever seen?",

    "Great! I like to share thoughts about movies! This Christmas I decided to try something unusual "
    "and watched Ring by Hideo Nakata. It was really scary! "
    "I still shudder when I remember this. How about you? What is the scariest movie you have ever seen?",

    "Good idea! I like TV shows. I like to relax and watch an episode of a good TV series after a hard day. "
    "What is your favorite TV series?",
]


ABOUT_MOVIE_PERSONS_PHRASES = [
    "What movie star would you most like to meet?",
    "Who is your favorite actor or actress?",
    "Who is your favorite director?",
    "Which famous person would you like to have for a best friend?",
]

PRAISE_ACTOR_TEMPLATES = [
    "The performance of {name} was outstanding!",
    "{name}'s acting was so subtle!",
    "The acting of {name} was exceptionally good!",
    "I was so impressed by {name}'s performance!",
]


PRAISE_VOICE_ACTOR_TEMPLATES = [
    "I love {name}'s voice! Great performance.",
    "I reckon {name} is great in voicing!",
]


TRY_PRAISE_DIRECTOR_OR_WRITER_OR_VISUALS = {
    "director": "I think the director {director} achieved a perfect chemistry between characters.",
    "writer": 'In my humble opinion the writer {writer} did a brilliant job creating such an intricate plot.',
    "visuals": "I was particularly impressed by visual part of the movie.",
}


def skill_trigger_phrases():
    return [SWITCH_MOVIE_SKILL_PHRASE] + ABOUT_MOVIE_TITLES_PHRASES


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


def praise_actor(name, animation):
    tmpl = choice(PRAISE_VOICE_ACTOR_TEMPLATES if animation else PRAISE_ACTOR_TEMPLATES)
    return tmpl.format(name=name)


def praise_director_or_writer_or_visuals(director, writer):
    if director is None:
        if writer is None:
            phrase = TRY_PRAISE_DIRECTOR_OR_WRITER_OR_VISUALS["visuals"]
        else:
            phrase = TRY_PRAISE_DIRECTOR_OR_WRITER_OR_VISUALS['writer'].format(
                writer=writer)
    else:
        if writer is None:
            phrase = TRY_PRAISE_DIRECTOR_OR_WRITER_OR_VISUALS['director'].format(
                director=director)
        else:
            praise_director = choice([True, False])
            if praise_director:
                phrase = TRY_PRAISE_DIRECTOR_OR_WRITER_OR_VISUALS['director'].format(
                    director=director)
            else:
                phrase = TRY_PRAISE_DIRECTOR_OR_WRITER_OR_VISUALS['writer'].format(
                    writer=writer)
    return phrase


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
