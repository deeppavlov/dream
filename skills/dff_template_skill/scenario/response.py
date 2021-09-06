import logging

from dff.core import Context, Actor
from .statistics import covid_data_server as cds

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
    template2 = "{0} is located in {1}. In this county, the total number of registered coronavirus " \
                "cases is {2} including {3} deaths."
    template3 = "In the {0}, {1}, the total number of registered coronavirus cases is {2} including {3} deaths."

    response = ""

    # see condition.subject_detected
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


def get_agephrase(age_num, bot_attr, human_attr):
    if age_num < 20:
        phrase = (
            "According to the statistical data, 999 persons from 1000 in your age "
            "recover after contacting coronavirus."
        )
    elif age_num < 40:  # prob = 0.2
        phrase = (
            "According to the statistical data, 499 persons from 500 "
            "in your age recover after contacting coronavirus."
        )
    elif age_num < 50:  # prob = 0.4
        phrase = (
            "According to the statistical data, 249 persons from 250 "
            "in your age recover after contacting coronavirus."
        )
    elif age_num < 60:  # prob = 1.3
        phrase = (
            "According to the statistical data, 76 persons from 77 " "in your age recover after contacting coronavirus."
        )
    elif age_num < 70:  # prob = 3.6
        phrase = (
            "According to the statistical data, 27 persons from 28 " "in your age recover after contacting coronavirus."
        )
    elif age_num < 80:  # prob = 8
        phrase = (
            "According to the statistical data, 12 persons from 13 " "of your age recover after contacting coronavirus."
        )
    else:  # prob = 13.6
        phrase = (
            "According to the statistical data, 7 persons from 8 " "of your age recover after contacting coronavirus."
        )
    phrase = f"{phrase} However, it is better to stay at home as much as you can " "to make older people safer."
    r = random()
    if r < 0.5:
        phrase = f"{phrase} While staying at home, you may use a lot of different online cinema. "
        link = link_to(["dff_movie_skill"], human_attributes=human_attr)
        human_attr["used_links"][link["skill"]] = human_attr["used_links"].get(link["skill"], []) + [link["phrase"]]
        phrase = f"{phrase} {link['phrase']}"
    else:
        phrase = f"{phrase} While staying at home, you may read a lot of different books. "
        link = link_to(["book_skill"], human_attributes=human_attr)
        human_attr["used_links"][link["skill"]] = human_attr["used_links"].get(link["skill"], []) + [link["phrase"]]
        phrase = phrase + link["phrase"]
    return phrase, bot_attr, human_attr


def tell_age_risks(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    response = ""

    age = ctx.misc.get("age", None)

    if not age:
        return response

    if age < 20:
        response = (
            "According to the statistical data, 999 persons from 1000 in your age "
            "recover after contacting coronavirus."
        )
    elif age < 40:  # prob = 0.2
        response = (
            "According to the statistical data, 499 persons from 500 "
            "in your age recover after contacting coronavirus."
        )
    elif age < 50:  # prob = 0.4
        response = (
            "According to the statistical data, 249 persons from 250 "
            "in your age recover after contacting coronavirus."
        )
    elif age < 60:  # prob = 1.3
        response = (
            "According to the statistical data, 76 persons from 77 " "in your age recover after contacting coronavirus."
        )
    elif age < 70:  # prob = 3.6
        response = (
            "According to the statistical data, 27 persons from 28 " "in your age recover after contacting coronavirus."
        )
    elif age < 80:  # prob = 8
        response = (
            "According to the statistical data, 12 persons from 13 " "of your age recover after contacting coronavirus."
        )
    else:  # prob = 13.6
        response = (
            "According to the statistical data, 7 persons from 8 " "of your age recover after contacting coronavirus."
        )

    response = f"{response} However, it is better to stay at home as much as you can to make older people safer."

    # here we should make link to the movie_skill or book_skill
    # but we do not have access to human_attributes.
    # see coronavirus_skill.scenario: 171-180 for more details

    return response



