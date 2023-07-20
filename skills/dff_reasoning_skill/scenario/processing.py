import json
from os import getenv
from df_engine.core import Context, Actor
import common.dff.integration.context as int_ctx

API_CONFIGS = getenv("API_CONFIGS", None)
API_CONFIGS = [] if API_CONFIGS is None else API_CONFIGS.split(",")
api_conf = {}
for config in API_CONFIGS:
    with open(f"api_configs/{config}", "r") as f:
        conf = json.load(f)
        api_conf.update(conf)


def save_user_answer():
    def save_slots_to_ctx_processing(
        ctx: Context,
        actor: Actor,
        *args,
        **kwargs,
    ) -> Context:
        slots = ctx.misc.get("slots", {})
        slots["details_answer"] = ctx.last_request
        ctx.misc["slots"] = slots
        return ctx

    return save_slots_to_ctx_processing


def save_approved_api():
    def save_slots_to_ctx_processing(
        ctx: Context,
        actor: Actor,
        *args,
        **kwargs,
    ) -> Context:
        slots = ctx.misc.get("slots", {})
        approved_tools = slots.get("approved_tools", [])
        shared_memory = int_ctx.get_shared_memory(ctx, actor)
        api2use = shared_memory.get("api2use", None)
        if api_conf[api2use]["needs_approval"] == "True":
            if api_conf[api2use]["approve_once"] == "True":
                if api2use not in approved_tools:
                    approved_tools.append(api2use)
        slots["approved_tools"] = approved_tools
        ctx.misc["slots"] = slots
        return ctx

    return save_slots_to_ctx_processing


def save_tries():
    def save_slots_to_ctx_processing(
        ctx: Context,
        actor: Actor,
        *args,
        **kwargs,
    ) -> Context:
        slots = ctx.misc.get("slots", {})
        tries = slots.get("tries", 1)
        tries += 1
        slots["tries"] = tries
        ctx.misc["slots"] = slots
        return ctx

    return save_slots_to_ctx_processing
