import logging
import random

from df_engine.core import Context, Actor

from tools.detectors import get_subject, get_age
from tools.statistics import covid_data_server as cds

logger = logging.getLogger(__name__)


def add_from_options(options):
    def add_from_options_handler(
        ctx: Context,
        actor: Actor,
        *args,
        **kwargs,
    ) -> Context:
        processed_node = ctx.a_s.get("processed_node", ctx.a_s["next_node"])
        processed_node.response = f"{processed_node.response} {random.choice(options)}"
        ctx.a_s["processed_node"] = processed_node
        return ctx

    return add_from_options_handler


def set_flag(flag: str, value: bool):
    def set_flag_handler(
        ctx: Context,
        actor: Actor,
        *args,
        **kwargs,
    ) -> Context:
        ctx.misc[flag] = value
        return ctx

    return set_flag_handler


def execute_response(
    ctx: Context,
    actor: Actor,
    *args,
    **kwargs,
) -> Context:
    processed_node = ctx.a_s.get("processed_node", ctx.a_s["next_node"])
    if callable(processed_node.response):
        processed_node.response = processed_node.response(ctx, actor)
    ctx.a_s["processed_node"] = processed_node

    return ctx


def offer_more(
    ctx: Context,
    actor: Actor,
    *args,
    **kwargs,
) -> Context:
    facts_exhausted = ctx.misc.get("covid_facts_exhausted", False)
    asked_about_age = ctx.misc.get("asked_about_age", False)

    # Because node.response can be empty string
    # (for example, when all covid facts are exhausted)
    def add_space(string: str):
        if string:
            return f"{string} "
        else:
            return string

    if facts_exhausted and asked_about_age:
        # do nothing
        return ctx
    processed_node = ctx.a_s.get("processed_node", ctx.a_s["next_node"])
    if callable(processed_node.response):
        try:
            response = processed_node.response(
                ctx,
                actor,
                *args,
                **kwargs,
            )
        except Exception as exc:
            logger.exception(exc)
            response = ""
    else:
        response = processed_node.response
    if not facts_exhausted:
        processed_node.response = f"{response} Would you want to learn more?"
        ctx.a_s["processed_node"] = processed_node
        return ctx
    if not asked_about_age:
        processed_node.response = (
            f"{response} Anyway, I can approximately tell you how likely you are to "
            f"recover from coronavirus if you get it. What is your age?"
        )
        ctx.a_s["processed_node"] = processed_node
        return ctx
    logger.critical("add_catch_question processor has reached an unreachable end in coronavirus_skill")
    return ctx


def insert_subject(
    ctx: Context,
    actor: Actor,
    *args,
    **kwargs,
) -> Context:
    # See condition.subject_detected for more details
    subject = ctx.misc.get(
        "subject",
        {
            "type": "country",
            "city": "undetected",
            "state": "undetected",
            "county": "undetected",
            "country": "undetected",
        },
    )
    processed_node = ctx.a_s.get("processed_node", ctx.a_s["next_node"])
    processed_node.response = processed_node.response.format(subject[subject["type"]])
    ctx.a_s["processed_node"] = processed_node

    return ctx


def insert_global_deaths(
    ctx: Context,
    actor: Actor,
    *args,
    **kwargs,
) -> Context:
    processed_node = ctx.a_s.get("processed_node", ctx.a_s["next_node"])
    processed_node.response = processed_node.response.format(cds.overall().deaths)
    ctx.a_s["processed_node"] = processed_node
    return ctx


def insert_global_confirmed(
    ctx: Context,
    actor: Actor,
    *args,
    **kwargs,
) -> Context:
    processed_node = ctx.a_s.get("processed_node", ctx.a_s["next_node"])
    processed_node.response = processed_node.response.format(cds.overall().confirmed)
    ctx.a_s["processed_node"] = processed_node
    return ctx


# See condition.subject_detected for performance note.
def detect_subject(
    ctx: Context,
    actor: Actor,
    *args,
    **kwargs,
) -> Context:
    subject = get_subject(ctx)

    if subject and subject["type"] != "undetected":
        ctx.misc["subject"] = subject

    return ctx


# See condition.subject_detected for performance note.
def detect_age(
    ctx: Context,
    actor: Actor,
    *args,
    **kwargs,
) -> Context:
    age = get_age(ctx)

    if age:
        ctx.misc["age"] = age

    return ctx
