import logging

from df_engine.core import Actor, Context
from scenario.response_funcs import get_respond_funcs
import common.utils as common_utils
import common.dff.integration.context as int_ctx

logger = logging.getLogger(__name__)


def command_selector_exists_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    if ctx.validation:
        return False

    intents_by_catcher = common_utils.get_intents(
        int_ctx.get_last_human_utterance(ctx, actor),
        probs=False,
        which="intent_catcher",
    )

    response_funcs = get_respond_funcs()
    return bool(any([intent in response_funcs for intent in intents_by_catcher]))
