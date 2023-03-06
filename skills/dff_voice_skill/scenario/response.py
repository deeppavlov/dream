import logging
import random 
from df_engine.core import Context, Actor
from common.dff.integration import condition as int_cnd
import common.dff.integration.context as int_ctx
import scenario.processing as loc_prs
from . import condition as loc_cnd

from df_engine.core import Context, Actor


logger = logging.getLogger(__name__)


def caption(ctx: Context, actor: Actor, excluded_skills=None, *args, **kwargs) -> str:
    cap = int_ctx.get_last_human_utterance(ctx, actor).get("annotations", {}).get("voice_service", {}).get("caption", ["No cap"])

    int_ctx.set_confidence(ctx, actor, 1)
    
    return f"Is there {cap} in that audio?"


def long_response(ctx: Context, actor: Actor, excluded_skills=None, *args, **kwargs) -> str:
    duration = int_ctx.get_last_human_utterance(ctx, actor).get("annotations", {}).get("voice_service", {}).get("sound_duration", ["0"])

    int_ctx.set_confidence(ctx, actor, 1)
    
    return f"Eine lange Nachricht - {duration} Sekunden"

    
def short_response(ctx: Context, actor: Actor, excluded_skills=None, *args, **kwargs) -> str:
    duration = int_ctx.get_last_human_utterance(ctx, actor).get("annotations", {}).get("voice_service", {}).get("sound_duration", ["0"])

    int_ctx.set_confidence(ctx, actor, 1)

    return f"I see a short message, my guy - {duration} seconds"