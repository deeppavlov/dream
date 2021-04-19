# %%

import json
import pathlib
import datetime
import traceback
import logging
import os
import argparse

import requests
import sentry_sdk

sentry_sdk.init(os.getenv("SENTRY_DSN"))
RAWG_API_KEY = os.getenv("RAWG_API_KEY")

logging.basicConfig(format="%(asctime)s - %(pathname)s - %(lineno)d - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--db", type=pathlib.Path)
args = parser.parse_args()

REQ_TIME_FORMAT = "%Y-%m-%d"
if not args.db.parent.is_dir():
    args.db.parent.mkdir(parents=True, exist_ok=True)
# %%

game_fields = [
    "id",
    "name",
    "name_original",
    "description",
    "released",
    "rating",
    "rating_top",
    "ratings",
    "reddit_url",
    "reddit_name",
    "reddit_description",
    "description_raw",
    "publishers",
    "genres",
    "user_game",
    "developers",
]


def get_game(game_id="99999999999"):
    try:
        game = requests.get(f"https://api.rawg.io/api/games/{game_id}?key={RAWG_API_KEY}").json()
        err_msg = f"empty response for game_id = {game_id}"
        assert game, err_msg
    except Exception as exc:
        logger.error(traceback.format_exc())
        sentry_sdk.capture_exception(exc)
        game = {}
    game = {field: game[field] for field in game_fields if field in game}
    return game


def get_game_top(from_data="2019-01-01", to_data="2019-12-31"):
    try:
        games = requests.get(
            f"https://api.rawg.io/api/games?dates={from_data},{to_data}&ordering=-added&key={RAWG_API_KEY}"
        )
        games = games.json()
        games = games.get("results", [])
        err_msg = f"empty response for game of ({from_data} {to_data})"
        assert games, err_msg
    except Exception as exc:
        logger.error(traceback.format_exc())
        sentry_sdk.capture_exception(exc)
        games = []
    games = [get_game(game["id"]) for game in games if "id" in game]
    return games


# it takes about 30 seconds
def download_data():
    curr_date = datetime.datetime.now()
    data = {}
    curr_year_begin = datetime.datetime(curr_date.now().year, 1, 1)
    previous_year_begin = curr_year_begin - datetime.timedelta(365)
    month_begin = curr_date - datetime.timedelta(31 + 7)
    # ep, there are 2 weeks instead one week because delay
    week_begin = curr_date - datetime.timedelta(7 + 7)
    curr_year_begin, previous_year_begin, month_begin, week_begin
    data["previous_yearly_top"] = get_game_top(
        from_data=previous_year_begin.strftime(REQ_TIME_FORMAT), to_data=curr_year_begin.strftime(REQ_TIME_FORMAT)
    )
    data["yearly_top"] = get_game_top(
        from_data=curr_year_begin.strftime(REQ_TIME_FORMAT), to_data=curr_date.strftime(REQ_TIME_FORMAT)
    )
    data["monthly_top"] = get_game_top(
        from_data=month_begin.strftime(REQ_TIME_FORMAT), to_data=curr_date.strftime(REQ_TIME_FORMAT)
    )
    data["weekly_top"] = get_game_top(
        from_data=week_begin.strftime(REQ_TIME_FORMAT), to_data=curr_date.strftime(REQ_TIME_FORMAT)
    )
    data = {
        time_range: [game for game in games if game.get("rating") and game.get("description_raw")]
        for time_range, games in data.items()
    }
    return data


def update_db_file(db_file_path):
    curr_date = datetime.datetime.now()
    min_update_time = datetime.timedelta(hours=12)
    file_modification_time = datetime.datetime.fromtimestamp(args.db.lstat().st_mtime if args.db.exists() else 0)
    if curr_date - min_update_time > file_modification_time:
        logger.info("Start game db updating")
        data = download_data()
        db_file_path = pathlib.Path(db_file_path)
        json.dump(data, db_file_path.open("wt"), indent=4, ensure_ascii=False)
        logger.info("Game db updating is finished")
    else:
        logger.info("Stop game db updating, db has already been updated")


if __name__ == "__main__":
    logger.info("Start game db creating")
    data = download_data()
    logger.info("Game db creating is finished")
    if sum(data.values(), []):
        json.dump(data, args.db.open("wt"), indent=4, ensure_ascii=False)
    else:
        exit(1)
