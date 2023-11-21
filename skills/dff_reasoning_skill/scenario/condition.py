import logging
import re
import json
from os import getenv

from df_engine.core import Actor, Context
import common.dff.integration.context as int_ctx
from common.utils import yes_templates


logger = logging.getLogger(__name__)


API_CONFIGS = getenv("API_CONFIGS", None)
API_CONFIGS = [] if API_CONFIGS is None else API_CONFIGS.split(",")
api_conf = {}
for config in API_CONFIGS:
    with open(f"api_configs/{config}", "r") as f:
        conf = json.load(f)
        api_conf.update(conf)


def is_last_utt_approval_question(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    if not ctx.validation:
        bot_uttr = int_ctx.get_last_bot_utterance(ctx, actor).get("text", "")
        if "Do you approve?" in bot_uttr:
            return True
    return False


def needs_details(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    if not ctx.validation:
        shared_memory = int_ctx.get_shared_memory(ctx, actor)
        answer = shared_memory.get("needs_details", "")
        if answer and re.search(yes_templates, answer.lower()):
            return True
    return False


def is_tool_needs_approval(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    if not ctx.validation:
        shared_memory = int_ctx.get_shared_memory(ctx, actor)
        api2use = shared_memory.get("api2use", None)
        if api2use:
            approved_tools = ctx.misc.get("slots", {}).get("approved_tools", [])
            if api_conf[api2use]["needs_approval"]:
                if api_conf[api2use]["approve_once"]:
                    if api2use not in approved_tools:
                        return True
                else:
                    return True
    return False


def is_self_reflection_ok(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    if not ctx.validation:
        shared_memory = int_ctx.get_shared_memory(ctx, actor)
        self_reflexion = shared_memory.get("self_reflexion", "")
        if self_reflexion and re.search(yes_templates, self_reflexion.lower()):
            return True
    return False


def is_last_step(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    if not ctx.validation:
        shared_memory = int_ctx.get_shared_memory(ctx, actor)
        step = shared_memory.get("step", 0)
        plan = shared_memory.get("plan", list())
        if int(step) == len(plan):
            return True
    return False


def is_tries_left(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    if not ctx.validation:
        tries = ctx.misc.get("slots", {}).get("tries", 1)
        if tries <= 3:
            return True
    return False
