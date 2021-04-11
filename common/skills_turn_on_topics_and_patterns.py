import re

from common.animals import ANIMALS_TEMPLATE, PETS_TEMPLATE
from common.books import BOOK_PATTERN
# from common.celebrities import CELEBRITY_COMPILED_PATTERN
from common.coronavirus import virus_compiled
from common.food import FOOD_COMPILED_PATTERN
from common.funfact import FUNFACT_COMPILED_PATTERN
from common.game_cooperative_skill import GAMES_COMPILED_PATTERN
from common.movies import MOVIE_COMPILED_PATTERN
from common.music import MUSIC_COMPILED_PATTERN
from common.news import NEWS_COMPILED_PATTERN
from common.sport import KIND_OF_SPORTS_TEMPLATE, SPORT_TEMPLATE, KIND_OF_COMPETITION_TEMPLATE, COMPETITION_TEMPLATE, \
    ATHLETE_TEMPLETE
from common.travel import TRAVELLING_TEMPLATE
from common.weather import WEATHER_COMPILED_PATTERN

SKILL_TOPICS = {
    "movie_skill": {
        "compiled_patterns": [MOVIE_COMPILED_PATTERN],
        "cobot_dialogact_topics": [
            "Entertainment_Movies",
            "Entertainment_General"
        ],
        "cobot_topics": [
            "Movies_TV",
            "Celebrities",
            "Art_Event",
            "Entertainment",
            "Fashion",
        ]
    },
    "book_skill": {
        "compiled_patterns": [BOOK_PATTERN],
        "cobot_dialogact_topics": [
            "Entertainment_General",
            "Entertainment_Books"
        ],
        "cobot_topics": [
            "Entertainment",
            "Literature"
        ]
    },
    "news_api_skill": {
        "compiled_patterns": [NEWS_COMPILED_PATTERN],
        "cobot_dialogact_topics": [
        ],
        "cobot_topics": [
            "News"
        ]
    },
    "dff_food_skill": {
        "compiled_patterns": [FOOD_COMPILED_PATTERN],
        "cobot_dialogact_topics": [
        ],
        "cobot_topics": [
            "Food_Drink"
        ]
    },
    "dff_animals_skill": {
        "compiled_patterns": [ANIMALS_TEMPLATE, PETS_TEMPLATE],
        "cobot_dialogact_topics": [
        ],
        "cobot_topics": [
            "Pets_Animals"
        ]
    },
    "dff_sport_skill": {
        "compiled_patterns": [SPORT_TEMPLATE, KIND_OF_SPORTS_TEMPLATE, KIND_OF_COMPETITION_TEMPLATE,
                              COMPETITION_TEMPLATE, ATHLETE_TEMPLETE],
        "cobot_dialogact_topics": [
            "Sports"
        ],
        "cobot_topics": [
            "Sports"
        ]
    },
    "dff_music_skill": {
        "compiled_patterns": [MUSIC_COMPILED_PATTERN],
        "cobot_dialogact_topics": [
            "Entertainment_Music"
        ],
        "cobot_topics": [
            "Music"
        ]
    },
    "dff_science_skill": {
        "compiled_patterns": [],
        "cobot_dialogact_topics": [
            "Science_and_Technology",
            "Entertainment_Books",
        ],
        "cobot_topics": [
            "Literature",
            "Math",
            "SciTech",
        ]
    },
    # "dff_celebrity_skill": {
    #     "compiled_patterns": [CELEBRITY_COMPILED_PATTERN],
    #     "cobot_dialogact_topics": [
    #     ],
    #     "cobot_topics": [
    #         "Celebrities"
    #     ]
    # },
    "game_cooperative_skill": {
        "compiled_patterns": [GAMES_COMPILED_PATTERN],
        "cobot_dialogact_topics": [
            "Entertainment_General"
        ],
        "cobot_topics": [
            "Games"
        ]
    },
    "weather_skill": {
        "compiled_patterns": [WEATHER_COMPILED_PATTERN],
        "cobot_dialogact_topics": [
        ],
        "cobot_topics": [
            "Weather_Time"
        ]
    },
    "dff_funfact_skill": {
        "compiled_patterns": [FUNFACT_COMPILED_PATTERN],
        "cobot_dialogact_topics": [
        ],
        "cobot_topics": [
        ]
    },
    "dff_travel_skill": {
        "compiled_patterns": [TRAVELLING_TEMPLATE],
        "cobot_dialogact_topics": [
        ],
        "cobot_topics": [
            "Travel_Geo"
        ]
    },
    "coronavirus_skill": {
        "compiled_patterns": [virus_compiled],
        "cobot_dialogact_topics": [
        ],
        "cobot_topics": [
        ]
    },
}


def turn_on_skills(cobot_topics, cobot_dialogact_topics, user_uttr_text, available_skills=None):
    cobot_dialogact_topics = set(cobot_dialogact_topics)
    cobot_topics = set(cobot_topics)

    skills = []
    for skill_name in SKILL_TOPICS:
        if available_skills is None or (available_skills is not None and skill_name in available_skills):
            for pattern in SKILL_TOPICS[skill_name]["compiled_patterns"]:
                if re.search(pattern, user_uttr_text):
                    skills.append(skill_name)
            if set(SKILL_TOPICS[skill_name]["cobot_dialogact_topics"]) & cobot_dialogact_topics:
                skills.append(skill_name)
            if set(SKILL_TOPICS[skill_name]["cobot_topics"]) & cobot_topics:
                skills.append(skill_name)
    return list(set(skills))
