import datetime
import os
import pickle
from typing import List, Union

from src.consts import NUM_NEWS_TO_PRINT
from src.content import format_headlines


def load(path):
    if os.path.isfile(path):
        with open(path, "rb") as f:
            return pickle.load(f)
    return None


def save(path, obj):
    with open(path, "wb") as f:
        pickle.dump(obj, f)
    return obj


def remove(path):
    if os.path.isfile(path):
        os.remove(path)


def datetime_from_text(date_text: str):
    try:
        return datetime.datetime.strptime(date_text, "%Y/%m/%d")
    except Exception as e:
        print(f"Exception: {e}")
        return None


def get_latest(
    texts: List[dict], return_indices: bool = False, num: int = NUM_NEWS_TO_PRINT
) -> Union[List[int], List[dict]]:
    dated_texts = []
    others = []
    for i, t in enumerate(texts):
        if "date" in t and datetime_from_text(t["date"]) is not None:
            dated_texts.append((i, t))
        else:
            others.append((i, t))

    dated_texts = sorted(
        dated_texts,
        key=lambda text: datetime_from_text(text[1]["date"]),
        reverse=True,
    )

    dated_texts.extend(others)
    out = [i for i, _ in dated_texts] if return_indices else [t for _, t in dated_texts]

    if len(out) >= num:
        out = out[:num]
    return out


def from_indices(texts: List[dict], indices: List[Union[str, int]]) -> List[dict]:
    return [texts[int(i)] for i in indices]


def format_output_from_news(latest: List[dict], mode: str, prefix: str) -> str:
    message = format_headlines(latest)
    news = [(n["headline"], n["contenturl"], n["date"]) for n in latest]
    output = (news, mode, prefix + message)
    return str(output)


def format_output_from_indices(texts: List[dict], indices: List[Union[int, str]], mode: str, prefix: str) -> str:
    texts = from_indices(texts, indices)
    latest = get_latest(texts)
    output = format_output_from_news(latest, mode, prefix)
    return output
