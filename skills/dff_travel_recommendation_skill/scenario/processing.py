import logging
import re
import json
import random

from df_engine.core import Node, Context, Actor


logger = logging.getLogger(__name__)
# ....

with open('common/places2visit.json', 'r') as f:
    where2go = json.load(f)


def choose_countries2recommend():
    def save_slots_to_ctx_processing(
        ctx: Context,
        actor: Actor,
        *args,
        **kwargs,
    ) -> Context:
        slots = ctx.misc.get("slots", {})
        countries = random.sample(list(where2go.keys()), 3)
        for i, country in enumerate(countries):
            slots['country' + str(i)] = country
            slots['capital' + str(i)] = where2go[country]['capital']
            slots['sight' + str(i)] = where2go[country]['sight']
            slots['description' + str(i)] = where2go[country]['description']
            slots['climate' + str(i)] = where2go[country]['climate']
            slots['best_time' + str(i)] = where2go[country]['best_time']

        ctx.misc["slots"] = slots
        return ctx

    return save_slots_to_ctx_processing
    