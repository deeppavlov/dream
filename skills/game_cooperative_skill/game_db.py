# %%

import json
import pathlib
import os
import datetime

import requests

DB_FILE = pathlib.Path(os.getenv("DB_FILE", "/tmp/game_db.json"))
REQ_TIME_FORMAT = "%Y-%m-%d"
if not DB_FILE.parent.is_dir():
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
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
        game = requests.get(f"https://api.rawg.io/api/games/{game_id}").json()
    except Exception:
        game = {}
    game = {field: game[field] for field in game_fields if field in game}
    return game


def get_game_top(from_data="2019-01-01", to_data="2019-12-31"):
    try:
        games = (
            requests.get(f"https://api.rawg.io/api/games?dates={from_data},{to_data}&ordering=-added")
            .json()
            .get("results", [])
        )
    except Exception:
        games = []
    games = [get_game(game["id"]) for game in games if "id" in game]
    return games


# it takes about 30 seconds
def download_data():
    curr_date = datetime.datetime.now()
    data = {}
    curr_year_begin = datetime.datetime(curr_date.now().year, 1, 1)
    previous_year_begin = curr_year_begin - datetime.timedelta(365)
    month_begin = curr_date - datetime.timedelta(31)
    week_begin = curr_date - datetime.timedelta(7)
    curr_year_begin, previous_year_begin, month_begin, week_begin
    data["previous_yearly_top"] = get_game_top(
        from_data=previous_year_begin.strftime(REQ_TIME_FORMAT), to_data=curr_year_begin.strftime(REQ_TIME_FORMAT)
    )
    data["yearly_top"] = get_game_top(
        from_data=curr_year_begin.strftime(REQ_TIME_FORMAT), to_data=curr_date.strftime(REQ_TIME_FORMAT)
    )
    data["monthly_top"] = get_game_top(
        from_data=week_begin.strftime(REQ_TIME_FORMAT), to_data=curr_date.strftime(REQ_TIME_FORMAT)
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
    file_modification_time = datetime.datetime.fromtimestamp(DB_FILE.lstat().st_mtime if DB_FILE.exists() else 0)
    if curr_date - min_update_time > file_modification_time:
        print("Start game db updating", flush=True)
        data = download_data()
        db_file_path = pathlib.Path(db_file_path)
        json.dump(data, db_file_path.open("wt"), indent=4, ensure_ascii=False)
        print("Game db updating is finished", flush=True)
    else:
        print("Stop game db updating, db has already been updated", flush=True)


if __name__ == "__main__":
    # execute only if run as a script
    update_db_file(DB_FILE)
