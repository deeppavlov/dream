import logging

from dff.core import Context, Actor

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
