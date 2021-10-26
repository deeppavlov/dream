from typing import Callable, Pattern, Tuple, Union, Any
import logging
import re

from pydantic import validate_arguments


from .core.actor import Actor
from .core.context import Context


logger = logging.getLogger(__name__)


@validate_arguments
def exact_match(match: Any, *args, **kwargs):
    def exact_match_condition_handler(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
        request = ctx.last_request
        try:
            return match == request
        except Exception as exc:
            logger.error(f"Exception {exc} for {match=} and {request=}", exc_info=exc)

    return exact_match_condition_handler


@validate_arguments
def regexp(pattern: Union[str, Pattern], flags: Union[int, re.RegexFlag] = 0, *args, **kwargs):
    pattern = re.compile(pattern, flags)

    def regexp_condition_handler(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
        request = ctx.last_request
        try:
            return bool(pattern.search(request))
        except Exception as exc:
            logger.error(f"Exception {exc} for {pattern=} and {request=}", exc_info=exc)

    return regexp_condition_handler


@validate_arguments
def check_cond_seq(cond_seq):
    for cond in cond_seq:
        if not isinstance(cond, Callable):
            raise Exception(f"{cond_seq=} has to consist of callable objects")


_any = any
_all = all


def aggregate(cond_seq: list, aggregate_func: Callable = _any, *args, **kwargs):
    check_cond_seq(cond_seq)

    def aggregate_condition_handler(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
        try:
            return bool(aggregate_func([cond(ctx, actor, *args, **kwargs) for cond in cond_seq]))
        except Exception as exc:
            logger.error(f"Exception {exc} for {cond_seq=}, {aggregate_func=} and {ctx.last_request=}", exc_info=exc)

    return aggregate_condition_handler


@validate_arguments
def any(cond_seq: list, *args, **kwargs):
    _agg = aggregate(cond_seq, _any)

    def any_condition_handler(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
        return _agg(ctx, actor, *args, **kwargs)

    return any_condition_handler


@validate_arguments
def all(cond_seq: list, *args, **kwargs):
    _agg = aggregate(cond_seq, _all)

    def all_condition_handler(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
        return _agg(ctx, actor, *args, **kwargs)

    return all_condition_handler


@validate_arguments
def negation(condition: Callable, *args, **kwargs):
    def negation_condition_handler(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
        return not condition(ctx, actor, *args, **kwargs)

    return negation_condition_handler


@validate_arguments
def isin_flow(flows: list[str] = [], nodes: list[Tuple[str, str]] = [], *args, **kwargs):
    def isin_flow_condition_handler(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
        node_label = list(ctx.node_labels.values())
        node_label = node_label[-1][:2] if node_label else (None, None)
        return node_label[0] in flows or node_label in nodes

    return isin_flow_condition_handler

@validate_arguments
def true(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    return True

@validate_arguments
def false(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    return False


# aliases
agg = aggregate
neg = negation
