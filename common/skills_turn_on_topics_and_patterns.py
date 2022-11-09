import re

from common.animals import ANIMALS_TEMPLATE, PETS_TEMPLATE
from common.books import BOOK_PATTERN
from common.gaming import GAMES_WITH_AT_LEAST_1M_COPIES_SOLD_COMPILED_PATTERN, VIDEO_GAME_WORDS_COMPILED_PATTERN
from common.gossip import HAVE_YOU_GOSSIP_TEMPLATE, GOSSIP_COMPILED_PATTERN
from common.coronavirus import virus_compiled
from common.food import FOOD_COMPILED_PATTERN, FOOD_SKILL_TRANSFER_PHRASES_RE
from common.funfact import FUNFACT_COMPILED_PATTERN
from common.game_cooperative_skill import GAMES_COMPILED_PATTERN
from common.movies import MOVIE_COMPILED_PATTERN
from common.music import MUSIC_COMPILED_PATTERN
from common.science import SCIENCE_COMPILED_PATTERN
from common.news import NEWS_COMPILED_PATTERN, TOPIC_NEWS_OFFER
from common.sport import (
    KIND_OF_SPORTS_TEMPLATE,
    SPORT_TEMPLATE,
    KIND_OF_COMPETITION_TEMPLATE,
    COMPETITION_TEMPLATE,
    ATHLETE_TEMPLETE,
)
from common.travel import TRAVELLING_TEMPLATE, HAVE_YOU_BEEN_TEMPLATE, I_HAVE_BEEN_TEMPLATE
from common.weather import WEATHER_COMPILED_PATTERN
from common.bot_persona import YOUR_FAVORITE_COMPILED_PATTERN


from common.minecraft.triggers import WHY_MINECRAFT, BUILD_OBJECT_MINECRAFT


MINECRAFT_COMPILED_PATTERN = re.compile(r'\bminecraft\b',
    re.IGNORECASE
)

SKILL_TRIGGERS = {
    "dff_movie_skill": {
        "compiled_patterns": [MOVIE_COMPILED_PATTERN],
        "previous_bot_patterns": [MOVIE_COMPILED_PATTERN],
        "cobot_dialogact_topics": ["Entertainment_Movies", "Entertainment_General"],
        "cobot_topics": [
            "Movies_TV",
            "Celebrities",
            "Art_Event",
            "Entertainment",
            "Fashion",
        ],
        "intents": [],
    },
    "dff_book_skill": {
        "compiled_patterns": [BOOK_PATTERN],
        "previous_bot_patterns": [BOOK_PATTERN],
        "cobot_dialogact_topics": ["Entertainment_General", "Entertainment_Books"],
        "cobot_topics": ["Religion", "Entertainment", "Literature"],
        "intents": [],
    },
    "news_api_skill": {
        "compiled_patterns": [NEWS_COMPILED_PATTERN],
        "previous_bot_patterns": TOPIC_NEWS_OFFER,
        "cobot_dialogact_topics": [],
        "cobot_topics": ["News"],
        "intents": [],
    },
    "dff_food_skill": {
        "compiled_patterns": [FOOD_COMPILED_PATTERN],
        "previous_bot_patterns": [],
        #[FOOD_SKILL_TRANSFER_PHRASES_RE, FOOD_COMPILED_PATTERN],
        "cobot_dialogact_topics": [],
        "cobot_topics": ["Food_Drink"],
        "intents": [],
    },
    "dff_gaming_skill": {
        "compiled_patterns": [GAMES_WITH_AT_LEAST_1M_COPIES_SOLD_COMPILED_PATTERN, VIDEO_GAME_WORDS_COMPILED_PATTERN],
        "previous_bot_patterns": [
            GAMES_WITH_AT_LEAST_1M_COPIES_SOLD_COMPILED_PATTERN,
            VIDEO_GAME_WORDS_COMPILED_PATTERN,
        ],
        "cobot_dialogact_topics": ["Entertainment_General"],
        "cobot_topics": ["Games"],
        "intents": [],
    },
    "dff_animals_skill": {
        "compiled_patterns": [ANIMALS_TEMPLATE, PETS_TEMPLATE],
        "previous_bot_patterns": [ANIMALS_TEMPLATE, PETS_TEMPLATE],
        "cobot_dialogact_topics": [],
        "cobot_topics": ["Pets_Animals"],
        "intents": [],
    },
    "dff_sport_skill": {
        "compiled_patterns": [
            SPORT_TEMPLATE,
            KIND_OF_SPORTS_TEMPLATE,
            KIND_OF_COMPETITION_TEMPLATE,
            COMPETITION_TEMPLATE,
            ATHLETE_TEMPLETE,
        ],
        "previous_bot_patterns": [SPORT_TEMPLATE],
        "cobot_dialogact_topics": ["Sports"],
        "cobot_topics": ["Sports"],
        "intents": [],
    },
    "dff_music_skill": {
        "compiled_patterns": [MUSIC_COMPILED_PATTERN],
        "previous_bot_patterns": [MUSIC_COMPILED_PATTERN],
        "cobot_dialogact_topics": ["Entertainment_Music"],
        "cobot_topics": ["Music"],
        "intents": [],
    },
    "dff_science_skill": {
        "compiled_patterns": [SCIENCE_COMPILED_PATTERN],
        "previous_bot_patterns": [SCIENCE_COMPILED_PATTERN],
        "cobot_dialogact_topics": [
            "Science_and_Technology",
            "Entertainment_Books",
        ],
        "cobot_topics": [
            "Literature",
            "Math",
            "SciTech",
        ],
        "intents": [],
    },
    "game_cooperative_skill": {
        "compiled_patterns": [GAMES_COMPILED_PATTERN],
        "previous_bot_patterns": [GAMES_COMPILED_PATTERN],
        "cobot_dialogact_topics": ["Entertainment_General"],
        "cobot_topics": ["Games"],
        "intents": [],
    },
    "dff_weather_skill": {
        "compiled_patterns": [WEATHER_COMPILED_PATTERN],
        "previous_bot_patterns": [WEATHER_COMPILED_PATTERN],
        "cobot_dialogact_topics": [],
        "cobot_topics": ["Weather_Time"],
        "intents": [],
    },
    "dff_funfact_skill": {
        "compiled_patterns": [FUNFACT_COMPILED_PATTERN],
        "previous_bot_patterns": [FUNFACT_COMPILED_PATTERN],
        "cobot_dialogact_topics": [],
        "cobot_topics": [],
        "intents": [],
    },
    "dff_travel_skill": {
        "compiled_patterns": [TRAVELLING_TEMPLATE],
        "previous_bot_patterns": [HAVE_YOU_BEEN_TEMPLATE, TRAVELLING_TEMPLATE, I_HAVE_BEEN_TEMPLATE],
        "cobot_dialogact_topics": [],
        "cobot_topics": ["Travel_Geo"],
        "intents": [],
    },
    "dff_gossip_skill": {
        "compiled_patterns": [],
        "previous_bot_patterns": [HAVE_YOU_GOSSIP_TEMPLATE, GOSSIP_COMPILED_PATTERN],
        "cobot_dialogact_topics": [],
        "cobot_topics": [],
        "intents": [],
    },
    "dff_coronavirus_skill": {
        "compiled_patterns": [virus_compiled],
        "previous_bot_patterns": [],
        "cobot_dialogact_topics": [],
        "cobot_topics": [],
        "intents": [],
    },
    "dff_bot_persona_skill": {
        "compiled_patterns": [YOUR_FAVORITE_COMPILED_PATTERN],
        "previous_bot_patterns": [],
        "cobot_dialogact_topics": [],
        "cobot_topics": [],
        "intents": [],
    },
    "dff_short_story_skill": {
        "compiled_patterns": [],
        "previous_bot_patterns": [],
        "cobot_dialogact_topics": [],
        "cobot_topics": [],
        "intents": ["tell_me_a_story"],
    },
    "dff_minecraft_skill": {
        "compiled_patterns": [MINECRAFT_COMPILED_PATTERN, WHY_MINECRAFT, BUILD_OBJECT_MINECRAFT],
        "previous_bot_patterns": [],
        "cobot_dialogact_topics": [],
        "cobot_topics": [],
        "intents": ["tell_me_a_story"],
    },
}


def turn_on_skills(
    cobot_topics, cobot_dialogact_topics, catched_intents, user_uttr_text, prev_bot_uttr_text, available_skills=None
):
    """
    Function to turn on skills from SKILL_TRIGGERS based on
        - Cobot-topics, list of corresponding topics is in SKILL_TRIGGERS[skill_name][cobot_topics],
        - Cobot-Dialogact-Topics, SKILL_TRIGGERS[skill_name][cobot_dialogact_topics],
        - list of patterns (compiled or not) or strings (then ase sensitive) to search in USER utterances,
                see SKILL_TRIGGERS[skill_name][compiled_patterns]
        - list of patterns (compiled or not) or strings (then ase sensitive) to search in PREV BOT utterances,
                see SKILL_TRIGGERS[skill_name][previous_bot_patterns]
        - list of intents catched by `intent_catcher`, see SKILL_TRIGGERS[skill_name][intents]
    """
    cobot_dialogact_topics = set(cobot_dialogact_topics)
    cobot_topics = set(cobot_topics)
    catched_intents = set(catched_intents)

    skills = []
    for skill_name in SKILL_TRIGGERS:
        if available_skills is None or (available_skills is not None and skill_name in available_skills):
            for pattern in SKILL_TRIGGERS[skill_name]["compiled_patterns"]:
                if re.search(pattern, user_uttr_text):
                    skills.append(skill_name)
            for pattern in SKILL_TRIGGERS[skill_name]["previous_bot_patterns"]:
                if re.search(pattern, prev_bot_uttr_text):
                    skills.append(skill_name)
            if set(SKILL_TRIGGERS[skill_name]["cobot_dialogact_topics"]) & cobot_dialogact_topics:
                skills.append(skill_name)
            if set(SKILL_TRIGGERS[skill_name]["cobot_topics"]) & cobot_topics:
                skills.append(skill_name)
            if set(SKILL_TRIGGERS[skill_name]["intents"]) & catched_intents:
                skills.append(skill_name)
    return list(set(skills))
