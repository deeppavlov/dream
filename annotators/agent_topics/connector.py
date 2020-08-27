import asyncio
import logging
import re
from os import getenv
from typing import Dict, Callable

import sentry_sdk

from common.movies import movie_skill_was_proposed
from common.news import is_breaking_news_requested
from common.books import book_skill_was_proposed
from common.weather import is_weather_requested

sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)


class RuleBasedTopicAnnotatorConnector:
    sensitive_topics = {"Politics", "Religion", "Sex_Profanity"}
    # `General_ChatIntent` sensitive in case when `?` in reply
    sensitive_dialogacts = {"Opinion_RequestIntent", "General_ChatIntent"}
    movie_cobot_dialogacts = {"Entertainment_Movies", "Sports", "Entertainment_Music", "Entertainment_General"}
    movie_cobot_topics = {
        "Movies_TV",
        "Celebrities",
        "Art_Event",
        "Entertainment",
        "Fashion",
        "Games",
        "Music",
        "Sports",
    }
    entertainment_cobot_dialogacts = {
        "Entertainment_Movies",
        "Entertainment_Music",
        "Entertainment_General",
        "Entertainment_Books",
    }
    entertainment_cobot_topics = {
        "Art_Event",
        "Celebrities",
        "Entertainment",
        "Games",
    }
    fashion_cobot_dialogacts = set()
    fashion_cobot_topics = {
        "Fashion",
    }
    science_cobot_dialogacts = {
        "Science_and_Technology",
        "Entertainment_Books",
    }
    science_cobot_topics = {
        "Literature",
        "Math",
        "SciTech",
    }
    science_cobot_dialogacts = {
        "Science_and_Technology",
        "Entertainment_Books",
    }
    science_cobot_topics = {
        "Literature",
        "Math",
        "SciTech",
    }
    # politic_cobot_dialogacts = {
    #     "Politics",
    # }
    # politic_cobot_topics = {
    #     "Politics",
    # }
    sport_cobot_dialogacts = {
        "Sports",
    }
    sport_cobot_topics = {
        "Sports",
    }
    animals_cobot_topics = {
        "Pets_Animals",
    }
    books_cobot_dialogacts = {"Entertainment_General", "Entertainment_Books"}
    books_cobot_topics = {"Entertainment", "Literature"}
    news_cobot_topics = {"News"}
    about_movie_words = re.compile(
        r"(movie|film|picture|series|tv[ -]?show|reality[ -]?show|netflix|\btv\b|"
        r"comedy|comedies|thriller|animation|anime|talk[ -]?show|cartoon|drama|"
        r"fantasy)"
    )

    async def send(self, payload: Dict, callback: Callable):
        try:
            dialog = payload["payload"]["states_batch"][0]

            user_uttr_text = dialog["human_utterances"][-1]["text"].lower()
            user_uttr_annotations = dialog["human_utterances"][-1]["annotations"]

            cobot_topics = set(user_uttr_annotations.get("cobot_topics", {}).get("text", []))

            cobot_dialogact_topics = set(user_uttr_annotations.get("cobot_dialogact_topics", {}).get("text", []))

            about_movies = self.movie_cobot_dialogacts & cobot_dialogact_topics
            about_music = ("Entertainment_Music" in cobot_dialogact_topics) | ("Music" in cobot_topics)
            about_games = "Games" in cobot_topics and "Entertainment_General" in cobot_dialogact_topics
            about_books = (self.books_cobot_dialogacts & cobot_dialogact_topics) | (
                self.books_cobot_topics & cobot_topics
            )

            #  topicalchat_tfidf_retrieval
            about_entertainments = (self.entertainment_cobot_dialogacts & cobot_dialogact_topics) | (
                self.entertainment_cobot_topics & cobot_topics
            )
            about_fashions = (self.fashion_cobot_dialogacts & cobot_dialogact_topics) | (
                self.fashion_cobot_topics & cobot_topics
            )
            # about_politics = (politic_cobot_dialogacts & cobot_dialogact_topics) | (sport_cobot_topics & cobot_topics)
            about_science_technology = (self.science_cobot_dialogacts & cobot_dialogact_topics) | (
                self.science_cobot_topics & cobot_topics
            )
            about_sports = (self.sport_cobot_dialogacts & cobot_dialogact_topics) | (
                self.sport_cobot_topics & cobot_topics
            )
            about_animals = self.animals_cobot_topics & cobot_topics

            prev_user_uttr_hyp = []
            prev_bot_uttr = {}

            if len(dialog["human_utterances"]) > 1:
                prev_user_uttr_hyp = dialog["human_utterances"][-2]["hypotheses"]

            if dialog["bot_utterances"]:
                prev_bot_uttr = dialog["bot_utterances"][-1]

            weather_city_slot_requested = any(
                [
                    hyp.get("weather_forecast_interaction_city_slot_requested", False)
                    for hyp in prev_user_uttr_hyp
                    if hyp["skill_name"] == "weather_skill"
                ]
            )

            about_weather = user_uttr_annotations["intent_catcher"].get("weather_forecast_intent", {}).get(
                "detected", False
            ) or (prev_bot_uttr.get("active_skill", "") == "weather_skill" and weather_city_slot_requested)
            about_weather = about_weather or is_weather_requested(prev_bot_uttr, dialog["human_utterances"][-1])
            news_re_expr = re.compile(r"(news|(what is|what ?'s)( the)? new|something new)")
            about_news = (self.news_cobot_topics & cobot_topics) or re.search(news_re_expr, user_uttr_text)
            about_news = about_news or is_breaking_news_requested(prev_bot_uttr, dialog["human_utterances"][-1])
            about_movies = (
                about_movies
                or movie_skill_was_proposed(prev_bot_uttr)
                or re.search(self.about_movie_words, prev_bot_uttr.get("text", "").lower())
            )
            about_books = about_books or book_skill_was_proposed(prev_bot_uttr) or "book" in user_uttr_text

            topics = {
                "news": bool(about_news),
                "movies": bool(about_movies),
                "music": bool(about_music),
                "books": bool(about_books),
                "games": bool(about_games),
                "weather": bool(about_weather),
                "entertainments": bool(about_entertainments),
                "fashions": bool(about_fashions),
                "science_technology": bool(about_science_technology),
                "sports": bool(about_sports),
                "animals": bool(about_animals)
            }

            # print(f"topics: {topics}", flush=True)
            asyncio.create_task(callback(task_id=payload["task_id"], response=topics))
        except Exception as e:
            logger.exception(e)
            sentry_sdk.capture_exception(e)
            asyncio.create_task(callback(task_id=payload["task_id"], response=e))
