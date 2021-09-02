import logging

from dff.core import Actor, Context

from common.funfact import FUNFACT_COMPILED_PATTERN

logger = logging.getLogger(__name__)


def random_funfact_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    request = ctx.last_request
    return bool(FUNFACT_COMPILED_PATTERN.search(request))


def thematic_funfact_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    request = ctx.last_request
    return bool(FUNFACT_COMPILED_PATTERN.search(request) and "about" in request)


def another_funfact_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    request = ctx.last_request
    return bool("other" in request)
