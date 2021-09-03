import logging

from dff.core import Context, Actor


logger = logging.getLogger(__name__)

COVID_FACTS = [
    "Only two dogs and two cats on the Earth have ever been diagnosed with coronavirus. "
    "Moreover, even dogs and cats who have coronavirus cannot transmit coronavirus to the human.",
    "Wearing face masks reduces your infection chance by 65%.",
    "Someone who has completed quarantine or has been released from isolation "
    "does not pose a risk of coronavirus infection to other people. "
    "Can you tell me what people love doing  when people are self-isolating?",
]


def example_response(reply: str):
    def example_response_handler(ctx: Context, actor: Actor, *args, **kwargs) -> str:
        return reply

    return example_response_handler


def get_covid_fact(ctx: Context, actor: Actor, *args, **kwargs) -> str:
    used_facts = ctx.misc.get("used_covid_facts", [])

    for idx, fact in enumerate(COVID_FACTS):
        if idx not in used_facts:
            used_facts.append(idx)
            return fact

    ctx.misc["covid_facts_exhausted"] = True
    return ""
