import logging
import common.dff.integration.context as int_ctx

from df_engine.core import Context, Actor


logger = logging.getLogger(__name__)


def caption(ctx: Context, actor: Actor, excluded_skills=None, *args, **kwargs) -> str:
    cap = "ERROR"
    if not ctx.validation:
        cap = (
            int_ctx.get_last_human_utterance(ctx, actor)
            .get("annotations", {})
            .get("voice_service", {})
            .get("captions", "No cap")
        )

    return f"Is there {cap} in that audio?"
