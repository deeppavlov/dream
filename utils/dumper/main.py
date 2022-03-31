import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple

import pandas as pd
import requests
from tqdm import tqdm

agent_url = f"{os.getenv('AGENT_URL')}/api/dialogs/"
dump_path = os.getenv("DUMP_PATH", "/data") / Path("data.csv")
finished_threshold = timedelta(hours=1)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
logger.addHandler(console_handler)


def get_ids(url: str, offset: str = "") -> List[str]:
    """Returns all available dialogs from the agent database."""
    resp = requests.get(f"{url}{offset}").json()
    dialog_ids, next_offset = resp["dialog_ids"], resp["next"]
    if next_offset is not None:
        dialog_ids.extend(get_ids(url, next_offset))
    return dialog_ids


def filter_ids(ids: list, file_path: Path) -> list:
    """Removes from the ids list dialogs that are present in the file."""
    if file_path.exists():
        df = pd.read_csv(file_path)  # TODO: Add chunking to limit RAM usage
        dumped_ids = set(df["dialog_id"])
        logger.info(f"There are {len(dumped_ids)} dialogs in the file.")
        ids = [dialog_id for dialog_id in ids if dialog_id not in dumped_ids]
    return ids


def get_dialog(url: str, dialog_id: str) -> Tuple[list, list, list, list, datetime]:
    """Get data from one dialog."""
    resp = requests.get(f"{url}{dialog_id}").json()
    date_finish = datetime.strptime(resp["date_finish"], "%Y-%m-%d %H:%M:%S.%f")
    text = [utt["text"] for utt in resp["utterances"]]
    time = [utt["date_time"] for utt in resp["utterances"]]
    user = [utt["user"]["user_type"] for utt in resp["utterances"]]
    d_id = [dialog_id] * len(resp["utterances"])
    return d_id, user, time, text, date_finish


def get_dialogs(url: str, dialog_ids: List[str]) -> pd.DataFrame:
    """Get dataframe containing multiple dialogs."""

    d_ids, users, times, texts = [], [], [], []
    skipped_dialogs = 0

    for dialog_id in tqdm(dialog_ids):  # TODO: Add chunking to limit RAM usage
        d_id, user, time, text, date_finish = get_dialog(url, dialog_id)
        if datetime.utcnow() - date_finish < finished_threshold:
            skipped_dialogs += 1
            continue
        d_ids.extend(d_id)
        users.extend(user)
        times.extend(time)
        texts.extend(text)

    if skipped_dialogs:
        logger.info(f"{skipped_dialogs} dialogues skipped because they haven't finished yet.")

    return pd.DataFrame.from_dict({"dialog_id": d_ids, "from": users, "time": times, "text": texts})


def main():
    dialog_ids = get_ids(agent_url)
    logger.info(f"There are {len(dialog_ids)} in the agent database.")
    dialog_ids = filter_ids(dialog_ids, dump_path)
    logger.info(f"{len(dialog_ids)} dialog(s) could be added to the file. Downloading dialogues...")
    dialogs_df = get_dialogs(agent_url, dialog_ids)
    dialogs_df.to_csv(dump_path, mode="a", header=not dump_path.exists(), index=False)
    logger.info("Dialogs dump finished")


if __name__ == "__main__":
    main()
