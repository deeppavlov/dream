import re
import json

with open('common/series.json', 'r') as f:
    series = json.load(f)
    series_keys = list(series.keys())
    series = []
    for key in series_keys:
        if '*' in key:
             key = key.replace('*', '\*')
        series.append(key)

    


RECOMMEND_SERIES_PATTERN = re.compile(r"\b(recommend .*? (series|serial)|what .*? (series|serial) would you suggest|what .*? (series|serial) should i|what .*? (series|serial) would you recommend)", re.IGNORECASE)

MENTIONS_KNOWN_SERIES_PATTERN = re.compile(r"\b(" + ("|".join(series) + ")"), re.IGNORECASE)

MENTIONS_NETFLIX = re.compile(r"netflix", re.IGNORECASE)