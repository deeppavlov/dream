import re
import json


with open('common/series.json', 'r') as f:
    series = json.load(f)
    series_keys = list(series.keys())
    series = []
    ignore_series = ['You', 'H', 'K', 'She', 'What If?']
    for key in series_keys:
        if '*' in key:
             key = key.replace('*', '\*')
        if key not in ignore_series:
            series.append(key)

    


RECOMMEND_SERIES_PATTERN = re.compile(r"\b((recommend|suggest).*? (series|serial)|what .*? (series|serial) would you (suggest|recommend)|what .*? (series|serial) should i|series.*?any recommendations?)", re.IGNORECASE)

MENTIONS_KNOWN_SERIES_PATTERN = re.compile(r"\b(" + ("|".join(series) + ")"), re.IGNORECASE)

MENTIONS_NETFLIX = re.compile(r"netflix", re.IGNORECASE)