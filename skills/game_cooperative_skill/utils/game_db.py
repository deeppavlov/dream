import os
import json
import pathlib
import datetime
import logging

import sentry_sdk

from utils.state import get_game_hash

sentry_sdk.init(os.getenv("SENTRY_DSN"))
logger = logging.getLogger(__name__)


# configuration
DB_FILE = pathlib.Path(os.getenv("DB_FILE", "/data/game-cooperative-skill/game_db.json"))
GAME_DB = {}


def load_game_db(safety=True):
    try:
        db = json.load(DB_FILE.open())
        GAME_DB.update(
            {
                "db": {key: [game for game in val if get_game_hash(game)] for key, val in db.items()},
                "index": {get_game_hash(game): game for game in sum(list(db.values()), [])},
                "update_dt": datetime.datetime.now(),
                "used_dt": datetime.datetime.now(),
            }
        )
    except Exception as exc:
        sentry_sdk.capture_exception(exc)
        logger.exception(exc)
        if not safety:
            raise exc


outdate_time = datetime.timedelta(hours=12)
cool_down_time = datetime.timedelta(minutes=20)


def update_game_db():
    curr_dt = datetime.datetime.now()
    update_time = curr_dt - GAME_DB["update_dt"]
    used_time = curr_dt - GAME_DB["used_dt"]
    if update_time > outdate_time and used_time > cool_down_time:
        load_game_db(safety=True)


load_game_db(safety=False)


def get_game_db():
    update_game_db()
    GAME_DB["used_dt"] = datetime.datetime.now()
    return GAME_DB["db"]


def get_db_index():
    update_game_db()
    GAME_DB["used_dt"] = datetime.datetime.now()
    return GAME_DB["index"]
