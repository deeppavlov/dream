import logging
import os

import requests
import sentry_sdk


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["Authorization"] = "Bearer " + self.token
        return r


client_id = "e448s0weusy75ni2yotyinkwsp9zhd"
client_secret = "mk5yld255btok04bh76uf9u8mphdmc"
client_token = ""


def extract_from_wiki_parser(wiki_parser_annotations):
    if wiki_parser_annotations:
        for wp_ann in wiki_parser_annotations:
            logger.info("dff_games.was_game_mentioned: annotations:\n" + str(wp_ann))
            for entity_title, triplets in wp_ann.items():
                logger.info("any items? " + str(triplets))

                for triplet in triplets.get("instance of", []):
                    logger.info("dff_games.was_game_mentioned: " + triplet[1])
                    if "video game" in triplet[1]:
                        logger.info("dff_games.was_game_mentioned: used wiki_parser data to identify game: Success")
                        return True

                if ["Q7889", "video game"] in triplets.get("instance of", []):
                    logger.info("dff_games.was_game_mentioned: used wiki_parser data to identify game: Success")
                    return True

                elif ["Q7058673", "video game series"] in triplets.get("instance of", []):
                    logger.info("dff_games.was_game_mentioned: used wiki_parser data to identify game: Success")
                    return True

    logger.info("dff_games.was_game_mentioned: used wiki_parser data to identify game: Failure")
    return False


def was_game_mentioned(human_utterance):
    wiki_parser_annotations = human_utterance["annotations"].get("wiki_parser", [])

    if extract_from_wiki_parser(wiki_parser_annotations):
        return True

    human_text = human_utterance["text"]
    logger.info("dff_games.was_game_mentioned: input text: " + human_text)

    game_mentions = extraction_game_mentions(human_text)

    if len(game_mentions) > 0:
        logger.info("dff_games.was_game_mentioned: used online IGDB API to identify game: Success")
        return True
    else:
        logger.info("dff_games.was_game_mentioned: used online IGDB API to identify game: Failure")

    logger.info("dff_games.was_game_mentioned: used both wiki_parser and IGDB API to identify game, but failed")
    return False


def extraction_game_mentions(human_text):
    default_results = []

    try:
        payload = {"client_id": client_id, "client_secret": client_secret, "grant_type": "client_credentials"}
        token_data = requests.post("https://id.twitch.tv/oauth2/token?", params=payload, timeout=0.5)
        client_token = token_data.json()["access_token"]

        if client_token:
            headers = {"Client-ID": client_id, "Accept": "application/json", "Content-Type": "text/plain"}
            search_body = 'fields *; search "' + human_text + '"; limit 50;'
            search_results = requests.post(
                "https://api.igdb.com/v4/search",
                auth=BearerAuth(client_token),
                headers=headers,
                data=search_body,
                timeout=0.5,
            )

        logger.info("dff_games.extraction_game_mentions: general success")
        return search_results.json()

    except requests.exceptions.RequestException as e:
        logger.info("dff_games.extraction_game_mentions: Requests failure.")
        logger.info(f"dff_games.extraction_game_mentions: Exception: {e}")
        return default_results
