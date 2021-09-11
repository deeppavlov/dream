import logging
from random import random

from dff.core import Context, Actor

import common.dff.integration.context as int_ctx
from tools.statistics import covid_data_server as cds

logger = logging.getLogger(__name__)

COVID_FACTS = [
    "Only two dogs and two cats on the Earth have ever been diagnosed with coronavirus. "
    "Moreover, even dogs and cats who have coronavirus cannot transmit coronavirus to the human.",
    "Wearing face masks reduces your infection chance by 65%.",
    "Someone who has completed quarantine or has been released from isolation "
    "does not pose a risk of coronavirus infection to other people. "
    "Can you tell me what people love doing when people are self-isolating?",
]


def example_response(reply: str):
    def example_response_handler(ctx: Context, actor: Actor, *args, **kwargs) -> str:
        return reply

    return example_response_handler


def append_previous(reply: str):
    def append_previous_handler(ctx: Context, actor: Actor, *args, **kwargs) -> str:
        return f"{ctx.last_response} {reply}"

    return append_previous_handler


def get_covid_fact(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    used_facts = ctx.misc.get("used_covid_facts", [])
    fact_to_use = -1
    result = ""

    for idx, fact in enumerate(COVID_FACTS):
        if idx not in used_facts:
            fact_to_use = idx
            result = fact
            break

    if fact_to_use != -1:
        used_facts.append(fact_to_use)
        ctx.misc["used_covid_facts"] = used_facts

    if len(used_facts) == len(COVID_FACTS):
        ctx.misc["covid_facts_exhausted"] = True

    return result


def tell_subject_stats(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    template1 = "The total number of registered coronavirus cases in {0} is {1} including {2} deaths."
    template2 = (
        "{0} is located in {1}. In this county, the total number of registered coronavirus "
        "cases is {2} including {3} deaths."
    )
    template3 = "In the {0}, {1}, the total number of registered coronavirus cases is {2} including {3} deaths."

    response = ""

    # See condition.subject_detected for more details.
    subject = ctx.misc.get("subject", None)

    if not subject:
        return response

    data = None

    if subject["type"] == "state":
        data = cds.state(subject["state"])
        response = template1.format(subject["state"], data.confirmed, data.deaths)
    elif subject["type"] == "city":
        data = cds.state(subject["state"])
        response = template2.format(subject["city"], subject["county"], data.confirmed, data.deaths)
    elif subject["type"] == "county":
        data = cds.county(subject["state"], subject["county"])
        response = template3.format(subject["county"], subject["state"], data.confirmed, data.deaths)
    elif subject["type"] == "country":
        data = cds.country(subject["country"])
        response = template1.format(subject["country"], data.confirmed, data.deaths)

    if data.deaths == 1:
        response = response.replace("1 deaths", "1 death")
    elif data.deaths == 0:
        response = response.replace("0 deaths", "no deaths")

    return response


def tell_age_risks(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    response = ""
    template = (
        "According to the statistical data, {non_vaccinated} persons from {non_vaccinated_per} in your "
        "age recover after contacting coronavirus if they are non-vaccinated and {vaccinated} "
        "from {vaccinated_per} if they are vaccinated."
    )

    age = ctx.misc.get("age", None)

    if not age:
        return response

    # Tuple is (x, y), where 'x' from 'y' persons are recovered from covid
    data = {"non_vaccinated": (0, 0), "vaccinated": (0, 0)}

    if age < 18:
        data = {"non_vaccinated": (999998, 100000), "vaccinated": (100000, 100000)}
    elif age < 20:
        data = {"non_vaccinated": (999998, 100000), "vaccinated": (99999, 100000)}
    elif age < 40:
        data = {"non_vaccinated": (9999, 10000), "vaccinated": (99999, 100000)}
    elif age < 60:
        data = {"non_vaccinated": (996, 1000), "vaccinated": (99999, 100000)}
    elif age < 70:
        data = {"non_vaccinated": (986, 1000), "vaccinated": (99999, 100000)}
    elif age < 80:
        data = {"non_vaccinated": (95, 100), "vaccinated": (99999, 100000)}
    else:
        data = {"non_vaccinated": (85, 100), "vaccinated": (99999, 100000)}

    _data = {}
    # Unpack tuples into separate dict keys
    for key, value in data.items():
        _data[key] = value[0]
        _data[key + "_per"] = value[1]

    response = template.format(**_data)
    response = f"{response} However, it is better to stay at home as much as you can to make older people safer."

    r = random()
    if r < 0.5:
        skill = "dff_movie_skill"
        response = f"{response} While staying at home, you may use a lot of different online cinema. "
    else:
        skill = "book_skill"
        response = f"{response} While staying at home, you may read a lot of different books. "

    # Here should be the phrase obtained from the link to the 'movie_skill' or the 'book_skill', but
    # function 'link_to' requires 'human_attr'. Is it deprecated?
    # See coronavirus_skill.scenario: 171-180 for more details.

    int_ctx.set_cross_link(ctx, actor, skill)

    return response
