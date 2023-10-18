import logging

from df_engine.core import Actor, Context

logger = logging.getLogger(__name__)
# ....


def no_document_in_use():
    def no_document_in_use_handler(ctx: Context, actor: Actor) -> bool:
        if ctx.validation:
            document_in_use = []
        else:
            document_in_use = (
                ctx.misc["agent"]["dialog"]["human_utterances"][-1]
                .get("user", {})
                .get("attributes", {})
                .get("documents_in_use", {})
            )
        return not bool(document_in_use)

    return no_document_in_use_handler
