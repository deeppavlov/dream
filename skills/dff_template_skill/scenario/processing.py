import logging
import random
from typing import Optional

from dff.core import Context, Actor, Node

logger = logging.getLogger(__name__)


def add_from_choice(options):
    def add_from_choice_handler(
            node_label: str,
            node: Node,
            ctx: Context,
            actor: Actor,
            *args,
            **kwargs,
    ) -> Optional[tuple[str, Node]]:
        node.response = f"{node.response} {random.choice(options)}"
        return node_label, node


def add_catch_question(
        node_label: str,
        node: Node,
        ctx: Context,
        actor: Actor,
        *args,
        **kwargs,
) -> Optional[tuple[str, Node]]:
    facts_exhausted = ctx.misc.get("facts_exhausted", True)
    asked_about_age = ctx.misc.get("asked_about_age", True)

    if facts_exhausted and asked_about_age:
        # do nothing
        return node_label, node

    if not facts_exhausted:
        node.response = f"{node.response} Would you want to learn more?"
        return node_label, node

    if not asked_about_age:
        node.response = f"{node.response} Anyway, I can approximately tell you how likely you are to recover from " \
                        f"coronavirus if you get it. What is your age?"
        return node_label, node

    logger.critical("add_catch_question processor has reached an unreachable end in coronavirus_skill")
    return node_label, node
