import json
import re
from glob import glob
from typing import List
import wget
import tarfile
import os
import sys
import logging

from nltk.tokenize import sent_tokenize

from src.consts import DATA_PATH


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def reduce_bodies(texts):
    for i, news in enumerate(texts):
        body = re.sub("[ \t\n]+", " ", news["body"])
        body = sent_tokenize(body)[:2]
        texts[i]["body"] = " ".join(body)
    return texts


def parse_date(news_piece):
    urls = news_piece["contenturl"]
    if "associatedbinaryurl" in news_piece:
        urls += "".join(news_piece["associatedbinaryurl"])

    date = re.search(r"/(19|20)[0-9]{2}/[0-1][0-9]/[0-3][0-9]/", urls)
    if date:
        return date.group(0)[1:-1]

    date = re.search(r"-(19|20)[0-9]{2}[0-1][0-9][0-3][0-9].html", urls)
    if date:
        date = date.group(0)[1:-5]
        date = f"{date[:4]}/{date[4:6]}/{date[6:]}"
        return date

    date = re.search(r"-[0-1][0-9]-[0-3][0-9]-(19|20)[0-9]{2}.html", urls)
    if date:
        date = date.group(0)[1:-5]
        date = f"{date[6:]}/{date[:2]}/{date[3:5]}"
        return date

    return None


def load_data() -> List[dict]:
    try:
        updated_data_url = "http://files.deeppavlov.ai/alexaprize_data/updated_washington_post_data.tar.gz"
        wget.download(updated_data_url, out="updated_washington_post_data.tar.gz")
        tf = tarfile.open("updated_washington_post_data.tar.gz")
        tf.extractall(path="/src/data/")
        os.remove("updated_washington_post_data.tar.gz")
    except Exception as e:
        print(f"Exception: {e}")

    news = []
    unique_bodies = set()
    for file_path in glob(DATA_PATH):
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            for news_piece in data.values():
                if "body" in news_piece and news_piece["body"].strip():
                    if news_piece["body"] not in unique_bodies and "http" in news_piece["contenturl"]:
                        news_piece["date"] = parse_date(news_piece)
                        if news_piece["date"] is not None:
                            unique_bodies.add(news_piece["body"])
                            news.append(news_piece)
        except json.decoder.JSONDecodeError as e:
            msg = f"Exception: {e}. File: {file_path}"
            print(msg, file=sys.stderr)  # For some reason logger may not work?
            logger.exception(msg)
            continue
            # raise e

    return news
