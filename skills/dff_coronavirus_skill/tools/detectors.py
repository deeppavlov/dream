from string import punctuation
from typing import Union

from dff.core import Context
from word2number.w2n import word_to_num

from tools.database import database as db


def get_subject(ctx: Context) -> Union[dict[str, str], None]:
    # subject detection is not perfect
    # due it's inability to discern
    # state name from country name,
    # cities with same name but in different counties
    # and etc.

    subject = {
        "type": "undetected",
        "city": "undetected",
        "state": "undetected",
        "county": "undetected",
        "country": "undetected",
    }

    for request in reversed(ctx.requests.values()):
        lower_req = request.lower()

        for sym in punctuation:
            lower_req = lower_req.replace(sym, " ")

        lower_req = f" {lower_req} "

        for country in db.countries():
            if f" {country.lower()} " in lower_req:
                subject["type"] = "country"
                subject["country"] = country
                return subject

        for state in db.states():
            if f" {state.lower()} " in lower_req:
                subject["type"] = "state"
                subject["state"] = state
                return subject

        for county in db.counties():
            if f" {county[1].lower()} " in lower_req:
                subject["type"] = "county"
                subject["state"] = county[0]
                subject["county"] = county[1]
                return subject

        for city in db.cities():
            if f" {city[2].lower()} " in lower_req:
                subject["type"] = "city"
                subject["state"] = city[0]
                subject["county"] = city[1]
                subject["city"] = city[2]
                return subject

    return None


def get_age(ctx: Context) -> Union[int, None]:
    age_num = None
    request = ctx.last_request

    for sym in punctuation:
        request = request.replace(sym, " ")

    words = request.split(" ")

    for word in words:
        if word.isdigit():
            age_num = int(word)

    try:
        if age_num is None:
            age_num = word_to_num(request)
        return age_num
    except Exception:
        return None
