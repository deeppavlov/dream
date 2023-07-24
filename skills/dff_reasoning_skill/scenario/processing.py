from df_engine.core import Context, Actor


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
