import logging

import json

from df_engine.core import Node, Context, Actor
import random

logger = logging.getLogger(__name__)
# ....

with open('common/series.json', 'r') as f:
    series = json.load(f)

with open('common/series_directors.json', 'r') as f:
    directors = json.load(f)


def extract_random_series2recommend():
    def save_slots_to_ctx_processing(
        ctx: Context,
        actor: Actor,
        *args,
        **kwargs,
    ) -> Context:
        slots = ctx.misc.get("slots", {})
        random_series = random.choice(list(series.keys()))
        random_series2 = random.choice(list(series.keys()))
        random_series3 = random.choice(list(series.keys()))
        slots['random_series2recommend'] = str(random_series)
        slots['random_description'] = series[random_series]['description']
        slots['random_duration'] = str(series[random_series]['duration'])
        slots['random_release'] = str(series[random_series]['year'])

        slots['random_series2recommend_2'] = str(random_series2)
        slots['random_description_2'] = series[random_series2]['description']
        slots['random_duration_2'] = series[random_series2]['duration']
        slots['random_release_2'] = str(series[random_series2]['year'])

        slots['random_series2recommend_3'] = str(random_series3)
        slots['random_description_3'] = series[random_series3]['description']
        slots['random_duration_3'] = series[random_series3]['duration']
        slots['random_release_3'] = str(series[random_series3]['year'])

        ctx.misc['slots'] = slots
        return ctx
    
    return save_slots_to_ctx_processing


def extract_known_series():
    def save_slots_to_ctx_processing(
        ctx: Context,
        actor: Actor,
        *args,
        **kwargs,
    ) -> Context:
        slots = ctx.misc.get("slots", {})
        ignore_series = ['You', 'H', 'K']
        for ser, value in series.items():
            if (ser.lower() in ctx.last_request.lower()) and (ser not in ignore_series):
                if (value['director'] in directors.keys()) and (len(directors[value['director']]) != 1):
                    for s in directors[value['director']]:
                        if s['title'].lower() != ser.lower():
                            slots['recommend_series'] = str(s['title']) + ' by the same director ' + value['director']
                            slots['recommend_description'] = s['description']
                            slots['recommend_duration'] = s['duration']
                            slots['recommend_release'] = str(s['year'])
                else:
                    random_series = random.choice(list(series.keys()))
                    slots['recommend_series'] = str(random_series)
                    slots['recommend_description'] = series[random_series]['description']
                    slots['recommend_duration'] = series[random_series]['duration']
                    slots['recommend_release'] = str(series[random_series]['year'])

        ctx.misc['slots'] = slots
        return ctx

    return save_slots_to_ctx_processing
    