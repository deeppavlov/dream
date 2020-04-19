# %%

import json
import pathlib
import os
import datetime

import requests

content_dir = pathlib.Path(os.getenv("CONTENT_PATH", "content"))
REQ_TIME_FORMAT = "%Y-%m-%d"
if not content_dir.is_dir():
    content_dir.mkdir(parents=True, exist_ok=True)
# %%
curr_date = datetime.datetime.now()
content_file = content_dir / f"tops_{curr_date.strftime('%Y-%m-%d')}.json"


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


def top_games(from_data="2019-01-01", to_data="2019-12-31"):
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


# %%
data = {}
curr_year_begin = datetime.datetime(curr_date.now().year, 1, 1)
previous_year_begin = curr_year_begin - datetime.timedelta(365)
month_begin = curr_date - datetime.timedelta(31)
week_begin = curr_date - datetime.timedelta(7)
curr_year_begin, previous_year_begin, month_begin, week_begin
data["previous_yearly_top"] = top_games(
    from_data=previous_year_begin.strftime(REQ_TIME_FORMAT), to_data=curr_year_begin.strftime(REQ_TIME_FORMAT)
)
data["yearly_top"] = top_games(
    from_data=curr_year_begin.strftime(REQ_TIME_FORMAT), to_data=curr_date.strftime(REQ_TIME_FORMAT)
)
data["monthly_top"] = top_games(
    from_data=week_begin.strftime(REQ_TIME_FORMAT), to_data=curr_date.strftime(REQ_TIME_FORMAT)
)
data["weekly_top"] = top_games(
    from_data=week_begin.strftime(REQ_TIME_FORMAT), to_data=curr_date.strftime(REQ_TIME_FORMAT)
)
# %%
data = {
    time_diapason: [game for game in games if game.get("rating") and game.get("description_raw")]
    for time_diapason, games in data.items()
}
# %%


json.dump(data, content_file.open("wt"), indent=4, ensure_ascii=False)
# %%
for k, v in data.items():
    print(f"--------------------------")
    print(f"{k} : {[i['name']for i in v]}")

# %%
