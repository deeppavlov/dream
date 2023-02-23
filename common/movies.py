import re
from random import choice

from common.fact_retrieval import topic_types
from common.utils import get_entities, get_topics, TOPIC_GROUPS


MOVIE_SKILL_CHECK_PHRASE = "the recent movie"


SWITCH_MOVIE_SKILL_PHRASE = (
    f"Great idea! " f"I watch a lot of movies online. " f"What is {MOVIE_SKILL_CHECK_PHRASE} you've watched?"
)


MOVIE_COMPILED_PATTERN = re.compile(
    r"(movie|film|picture|series|tv[ -]?show|reality[ -]?show|netflix|\btv\b|"
    r"comedy|comedies|thriller|animation|anime|talk[ -]?show|cartoon|drama|"
    r"fantasy|watch\b|watching\b|watched\b|youtube|\byou tube\b)",
    re.IGNORECASE,
)
RECOMMEND_REQUEST_PATTERN = re.compile(
    r"(recommend|advice|suggest)( me)?[a-z0-9 ]+"
    r"(movie|series|\bshow\b|\btv\b|\bcomed|\bthriller|animation|cartoon|drama|\bfantas|\bwatch)",
    re.IGNORECASE,
)
RECOMMEND_OFFER_PATTERN = re.compile(
    r"(\bi\b|\bme\b)( to)? (recommend|advice) you[a-z0-9 ]+"
    r"(movie|series|\bshow\b|\btv\b|\bcomed|\bthriller|animation|cartoon|drama|\bfantas|\bwatch)",
    re.IGNORECASE,
)
NOT_LIKE_NOT_WATCH_MOVIES_TEMPLATE = re.compile(
    r"(don't|do not|not) (watch|watching|like) (movie|film|picture|series|"
    r"tv[ -]?show|reality[ -]?show|netflix|\btv\b|comedy|comedies|thriller|"
    r"animation|anime|talk[ -]?show|cartoon)",
    re.IGNORECASE,
)

NOT_WATCHED_TEMPLATE = re.compile(r"(have|'ve|did|was|had|were)? ?(never|not|n't) (seen|watch)", re.IGNORECASE)

RECOMMEND_OFFER_RESPONSE = [
    "Would you like me to recommend you a MOVIE?",
    "May I recommend you a MOVIE?",
    "Can I recommend you a MOVIE?",
]
RECOMMENDATION_PHRASES = [
    "I encourage you to watch MOVIE released in YEAR. It has RATING rating for NUM_VOTES votes. Have you seen it?",
    "I urge you to go and watch MOVIE released in YEAR. It has RATING rating for NUM_VOTES votes. Have you seen it?",
    "I highly commend you to watch MOVIE released in YEAR, with RATING rating for NUM_VOTES votes. Have you seen it?",
]
REPEAT_RECOMMENDATION_PHRASES = ["Okay. Then don't forget: MOVIE released in YEAR."]
WOULD_YOU_LIKE_TO_CONTINUE_TALK_ABOUT_MOVIES = [
    "Would you like to continue our conversation about movies?",
    "Would you like to continue to chat about movies?",
    "Do you want to continue to talk about movies?",
]


ABOUT_MOVIE_TITLES_PHRASES = [
    # "What is the name of the last movie you watched?",
    "What is the best movie you have seen recently?",
    # "What is the funniest movie you have ever seen?",
    "What movie you could watch over and over again?",
    # "What is the most romantic movie you have ever seen?",
    # "What is the scariest movie you have ever seen?",
    "What is your favorite TV series?",
    # "What TV show are you watching these days?",
    "What TV series did you watch on weekends?",
    # "What TV show do you watch when you need to escape the real world?",
    "What movie did you watch on weekends?",
]

WHAT_IS_YOUR_FAVORITE_MOMENT_PHRASES = [
    "Do you remember how 'MOMENT'? Did you like this movie moment?",
    "Remember how 'MOMENT'? I suppose, you like this moment?",
    "Do you think that when 'MOMENT' was one of the most impressive moments?",
]

WHAT_IS_YOUR_FAVORITE_MOMENT_NO_PLOT_FOUND_PHRASES = [
    "Did you like how characters developed through?",
    "Do you think the background of the filming made a significant contribution to the picture?",
    "Did you like the soundtrack?",
]

WHAT_OTHER_MOVIE_TO_DISCUSS = "What other movie you'd like to discuss?"
CLARIFY_WHAT_MOVIE_TO_DISCUSS = "Can you say again what movie you'd like to discuss?"
CELEB_ACTOR_PHRASES = ["What is your favourite movie with this actor?"]
WHAT_MOVIE_RECOMMEND = "What movie can you recommend to your friends?"


def skill_trigger_phrases():
    return [SWITCH_MOVIE_SKILL_PHRASE] + ABOUT_MOVIE_TITLES_PHRASES + [WHAT_MOVIE_RECOMMEND]


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
    "writer": "In my humble opinion the writer {writer} did a brilliant job creating such an intricate plot.",
    "visuals": "I was particularly impressed by visual part of the movie.",
}

DIFFERENT_SCRIPT_TEMPLATES = {
    "never_heard_about_template": [
        "I've never heard about SUBJECT before.",
        "I've never heard about SUBJECT previously.",
    ],
    "opinion_request_about_movie": [
        "What do you think about this TYPE?",
        "What is your view on this TYPE?",
        "What is your opinion on this TYPE?",
    ],
    "heard_about_template": [
        "Yeah, I've heard about SUBJECT,",
        "Yeah, I know SUBJECT,",
        "I've got what you are talking about.",
    ],
    "clarification_template": [
        "Did I get correctly that you are talking about",
        "Am I right in thinking that you are talking about",
        "Did I get correctly that you meant",
        "Am I right in thinking that you meant",
    ],
    "sorry_didnt_get_title": [
        "Sorry, I could not get what TYPE you are talking about.",
        "Sorry, I didn't get what TYPE you meant.",
    ],
    "lets_talk_about_other_movie": [
        "Let's talk about some other movie.",
        "Maybe you want to talk about some other movie.",
        "Do you want to discuss some other movie.",
    ],
    "user_opinion_comment": {
        "positive": ["Cool!", "Great!", "Nice!"],
        "neutral": ["Okay.", "Well.", "Hmm.."],
        "negative": ["I see.", "That's okay.", "Okay."],
    },
    "didnt_get_movie_title_at_all": [
        "Sorry, I didn't get the title, could you, please, repeat it.",
        "Sorry, I didn't understand the title, could you, please, repeat it.",
        "Sorry, I didn't catch the title, could you, please, repeat it.",
        "Sorry, I didn't get the title, can you, please, repeat it.",
    ],
    "dont_know_movie_title_at_all": [
        "Sorry, probably I've never heard about this TYPE.",
        "Sorry, maybe I just have never heard about this TYPE.",
        "Well, probably I've never heard about this TYPE.",
    ],
    "lets_move_on": ["Let's move on.", "Okay.", "Hmmm.", "Huh.", "Aha.", ""],
    "can_you_imagine": ["Did you know that", "Can you imagine that", "Have you heard that"],
}

ACKNOWLEDGEMENT_LIKES_MOVIE = [
    "So cool! I like it too! You have a good eye in movies.",
    "Great! Seems like you're well versed in movies.",
    "You've got a pretty sophisticated knowledge of movies.",
    "I'm glad you like it, it's a really nice film.",
    "Amazing! Agree with you! You have a excellent eye in movies.",
    "Wow! I see you're perfectly versed in movies.",
    "Yeah, it's a really amazing film.",
]


def get_movie_template(category, subcategory=None, movie_type="movie"):

    if subcategory is not None:
        return (
            choice(DIFFERENT_SCRIPT_TEMPLATES[category].get(subcategory, ""))
            .replace("TYPE", movie_type)
            .replace("SUBJECT", choice(["it", f"this {movie_type}"]))
        )
    else:
        return (
            choice(DIFFERENT_SCRIPT_TEMPLATES[category])
            .replace("TYPE", movie_type)
            .replace("SUBJECT", choice(["it", f"this {movie_type}"]))
        )


def praise_actor(name, animation):
    tmpl = choice(PRAISE_VOICE_ACTOR_TEMPLATES if animation else PRAISE_ACTOR_TEMPLATES)
    return tmpl.format(name=name)


def praise_director_or_writer_or_visuals(director, writer):
    if director is None:
        if writer is None:
            phrase = TRY_PRAISE_DIRECTOR_OR_WRITER_OR_VISUALS["visuals"]
        else:
            phrase = TRY_PRAISE_DIRECTOR_OR_WRITER_OR_VISUALS["writer"].format(writer=writer)
    else:
        if writer is None:
            phrase = TRY_PRAISE_DIRECTOR_OR_WRITER_OR_VISUALS["director"].format(director=director)
        else:
            praise_director = choice([True, False])
            if praise_director:
                phrase = TRY_PRAISE_DIRECTOR_OR_WRITER_OR_VISUALS["director"].format(director=director)
            else:
                phrase = TRY_PRAISE_DIRECTOR_OR_WRITER_OR_VISUALS["writer"].format(writer=writer)
    return phrase


def extract_movies_names_from_annotations(annotated_uttr, check_full_utterance=False):
    movies_titles = None
    if "entity_detection" in annotated_uttr["annotations"]:
        movies_titles = []
        entities = get_entities(annotated_uttr, only_named=False, with_labels=True)
        for ent in entities:
            if ent.get("label", "") == "videoname":
                movies_titles += [ent["text"]]

    # for now let's remove full utterance check but add entity_linking usage!
    if not movies_titles:
        # either None or empty list
        if "wiki_parser" in annotated_uttr["annotations"]:
            movies_titles = []
            for ent_name, ent_dict in annotated_uttr["annotations"]["wiki_parser"].get("entities_info", {}).items():
                instance_of_types = [el[0] for el in ent_dict.get("instance of", [])]
                instance_of_types += [el[0] for el in ent_dict.get("types_2hop", [])]
                if (
                    len(set(instance_of_types).intersection(set(topic_types["film"]))) > 0
                    and ent_dict.get("token_conf", 0.0) >= 0.5
                    and ent_dict.get("conf", 0.0) >= 0.5
                ):
                    movies_titles += [ent_dict.get("entity_label", ent_name).lower()]

    # if check_full_utterance:
    #     movies_titles += [re.sub(r"[\.\?,!]", "", annotated_uttr["text"]).strip()]
    return movies_titles


def about_movies(annotated_utterance):
    found_topics = get_topics(annotated_utterance, probs=False, which="all")
    if any([topic in found_topics for topic in TOPIC_GROUPS["movies"]]):
        return True
    elif re.findall(MOVIE_COMPILED_PATTERN, annotated_utterance["text"]):
        return True
    else:
        return False
