import logging
from dff.core import Actor, Context, Node

logger = logging.getLogger(__name__)


def predetermined_condition(condition: bool):
    # wrapper for internal condition function
    def internal_condition_function(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
        # It always returns `condition`.
        return condition

    return internal_condition_function
