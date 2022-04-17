import logging
import os
import random

from df_engine.core import Context, Actor


def set_goal_status_flag(status_flag):
    def update_goal_status(ctx: Context, actor: Actor):
        if not ctx.validation:
            ctx.misc["agent"]["response"].update({"goal_status": status_flag})
        return ctx
    
    return update_goal_status
