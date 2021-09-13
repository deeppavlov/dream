import logging
from typing import Optional

from dff.core import Actor, Context, Node

from common.dff.integration.context import set_confidence

logger = logging.getLogger(__name__)

CONF_ZERO = 0.0


def fallback_processing(
    node_label: str,
    node: Node,
    ctx: Context,
    actor: Actor,
    *args,
    **kwargs,
) -> Optional[tuple[str, Node]]:
    set_confidence(ctx, actor, CONF_ZERO)
    return node_label, node
