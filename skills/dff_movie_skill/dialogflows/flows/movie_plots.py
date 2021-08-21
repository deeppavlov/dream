import logging
import os
import requests
from typing import Tuple

import pandas as pd
import sentry_sdk

from dialogflows.flows.imdb_database import IMDb


sentry_sdk.init(os.getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

KNOWLEDGE_GROUNDING_SERVICE_URL = os.getenv("KNOWLEDGE_GROUNDING_SERVICE_URL")

SUPER_CONFIDENCE = 1.0


class MoviePlots:
    def __init__(self, imdb: IMDb):
        self.imdb = imdb
        self.WikiPlots_df = pd.read_csv("/data/movie_plots/WikiPlots.csv").set_index("Title")
        self.Wikipedia_Movie_Plots_df = pd.read_csv("/data/movie_plots/Wikipedia_Movie_Plots.csv").set_index("Title")

    def get_plot(self, imdb_id):
        names = self.imdb.get_movie_names(imdb_id)
        plot = None
        for n in names:
            if n in self.WikiPlots_df.index:
                plot = self.WikiPlots_df.loc[n, "Plot"]
                break
            if n in self.Wikipedia_Movie_Plots_df.index:
                plot = self.Wikipedia_Movie_Plots_df.loc[n, "Plot"]
                break
        if plot is None:
            logger.info(f"(MoviePlots.get_plot)None of movies {names} was found in movie plot dataframes")
        elif not isinstance(plot, str):
            plot = plot.values[0]  # if several plots in table, take first appeared
        else:
            logger.info(f"(MoviePlots.get_plot)for movies names {names} plot was found.")
        return plot

    def create_what_is_your_favorite_moment_in_movie_batch(self, user_input_history, plot, movie_name):
        what_is_your_favorite_phrases = [
            f"What is your favorite moment in the movie '{movie_name}'?",
            f"What do your like about the movie '{movie_name}'?",
            f"What do you find interesting in the movie '{movie_name}'?",
            f"Why do you like the movie '{movie_name}'?",
        ]
        batch = []
        for question in what_is_your_favorite_phrases:
            batch.append(
                {
                    "checked_sentence": plot,
                    "knowledge": plot,
                    "text": question,
                    "history": user_input_history,
                    "movie_plot": True,
                }
            )
        return batch

    def select_best_favorite_moment_and_assign_confidence(self, raw_responses):
        best_response = None
        for r in raw_responses:
            if "favorite" in r:
                best_response = r
        if best_response is None:
            best_response = raw_responses[0]
        confidence = SUPER_CONFIDENCE
        return best_response, confidence

    def movie_plot_is_available(self, imdb_id):
        names = self.imdb.get_movie_names(imdb_id)
        for n in names:
            if n in self.WikiPlots_df.index:
                return True
            if n in self.Wikipedia_Movie_Plots_df.index:
                return True
        return False

    def generate_bot_favorite_moment_in_movie(self, movie_id: str, dialog: dict) -> Tuple[str, float]:
        plot = self.get_plot(movie_id)
        user_input_history = "\n".join([i["text"] for i in dialog["utterances"]])
        movie_name = self.imdb(movie_id)["title"]
        batch = self.create_what_is_your_favorite_moment_in_movie_batch(user_input_history, plot, movie_name)
        try:
            resp = requests.post(KNOWLEDGE_GROUNDING_SERVICE_URL, json={"batch": batch}, timeout=1.5)
            raw_responses = resp.json()
            response, confidence = self.select_best_favorite_moment_and_assign_confidence(raw_responses)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            logger.exception(e)
            response = ""
            confidence = 0.0
        return response, confidence

    def discuss_plot(self, plot, history, input_text):
        history = "\n".join(history)
        batch = [
            {
                "checked_sentence": plot,
                "knowledge": plot,
                "text": input_text,
                "history": history,
                "movie_plot": True,
            }
        ]
        try:
            resp = requests.post(KNOWLEDGE_GROUNDING_SERVICE_URL, json={"batch": batch}, timeout=15.0)
            logger.info(f"(discuss_plot)resp: {repr(resp)}")
            raw_responses = resp.json()
            response = raw_responses[0]
            confidence = SUPER_CONFIDENCE
        except Exception as e:
            sentry_sdk.capture_exception(e)
            logger.exception(e)
            response = ""
            confidence = 0.0
        return response, confidence
