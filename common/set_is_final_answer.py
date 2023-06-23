from df_engine.core import Context, Actor


def set_is_final_answer_flag(is_final_answer_flag):
    def update_is_final_answer(ctx: Context, actor: Actor):
        if not ctx.validation:
            ctx.misc["agent"]["response"].update({"is_final_answer": is_final_answer_flag})
        return ctx

    return update_is_final_answer
