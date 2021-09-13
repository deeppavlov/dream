import logging
import random
from typing import Optional

from dff.core import Context, Actor, Node

from tools.detectors import get_subject, get_age
from tools.statistics import covid_data_server as cds

logger = logging.getLogger(__name__)


def add_from_options(options):
    def add_from_options_handler(
        node_label: str,
        node: Node,
        ctx: Context,
        actor: Actor,
        *args,
        **kwargs,
    ) -> Optional[tuple[str, Node]]:
        node.response = f"{node.response} {random.choice(options)}"
        return node_label, node

    return add_from_options_handler


def set_flag(flag: str, value: bool):
    def set_flag_handler(
        node_label: str,
        node: Node,
        ctx: Context,
        actor: Actor,
        *args,
        **kwargs,
    ) -> Optional[tuple[str, Node]]:
        ctx.misc[flag] = value
        return node_label, node

    return set_flag_handler


def execute_response(
    node_label: str,
    node: Node,
    ctx: Context,
    actor: Actor,
    *args,
    **kwargs,
) -> Optional[tuple[str, Node]]:
    if callable(node.response):
        node.response = node.response(ctx, actor)

    return node_label, node


def offer_more(
    node_label: str,
    node: Node,
    ctx: Context,
    actor: Actor,
    *args,
    **kwargs,
) -> Optional[tuple[str, Node]]:
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
        return node_label, node

    if not facts_exhausted:
        node.response = f"{add_space(node.response)}Would you want to learn more?"
        return node_label, node

    if not asked_about_age:
        node.response = (
            f"{add_space(node.response)}Anyway, I can approximately tell you how likely you are to "
            f"recover from coronavirus if you get it. What is your age?"
        )
        return node_label, node

    logger.critical("add_catch_question processor has reached an unreachable end in coronavirus_skill")
    return node_label, node


def insert_subject(
    node_label: str,
    node: Node,
    ctx: Context,
    actor: Actor,
    *args,
    **kwargs,
) -> Optional[tuple[str, Node]]:
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

    node.response = node.response.format(subject[subject["type"]])
    return node_label, node


def insert_global_deaths(
    node_label: str,
    node: Node,
    ctx: Context,
    actor: Actor,
    *args,
    **kwargs,
) -> Optional[tuple[str, Node]]:
    node.response = node.response.format(cds.overall().deaths)
    return node_label, node


def insert_global_confirmed(
    node_label: str,
    node: Node,
    ctx: Context,
    actor: Actor,
    *args,
    **kwargs,
) -> Optional[tuple[str, Node]]:
    node.response = node.response.format(cds.overall().confirmed)
    return node_label, node


# See condition.subject_detected for performance note.
def detect_subject(
    node_label: str,
    node: Node,
    ctx: Context,
    actor: Actor,
    *args,
    **kwargs,
) -> Optional[tuple[str, Node]]:
    subject = get_subject(ctx)

    if subject and subject["type"] != "undetected":
        ctx.misc["subject"] = subject

    return node_label, node


# See condition.subject_detected for performance note.
def detect_age(
    node_label: str,
    node: Node,
    ctx: Context,
    actor: Actor,
    *args,
    **kwargs,
) -> Optional[tuple[str, Node]]:
    age = get_age(ctx)

    if age:
        ctx.misc["age"] = age

    return node_label, node
