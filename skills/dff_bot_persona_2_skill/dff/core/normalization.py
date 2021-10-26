import logging

# from typing import ForwardRef
from typing import Union, Callable, Pattern, Optional, Any


from .context import Context

from pydantic import conlist, validate_arguments, BaseModel


logger = logging.getLogger(__name__)
# TODO: add texts

CONDITION_DEPTH_TYPE_CHECKING = 20
# Callable = str
# Pattern = str

NodeLabelTupledType = Union[
    tuple[str, float],
    tuple[str, str],
    tuple[str, str, float],
]
NodeLabelType = Union[Callable, NodeLabelTupledType, str]
ConditionType = Union[Callable, Pattern, str]
for _ in range(CONDITION_DEPTH_TYPE_CHECKING):
    ConditionType = Union[conlist(ConditionType, min_items=1), Callable, Pattern, str]


Actor = BaseModel  # ForwardRef("Actor")
Node = BaseModel  # ForwardRef("Node")


@validate_arguments
def normalize_node_label(
    node_label: NodeLabelType, flow_label: str, default_transition_priority: float
) -> Union[Callable, tuple[str, str, float]]:
    if isinstance(node_label, Callable):

        @validate_arguments
        def get_node_label_handler(ctx: Context, actor: Actor, *args, **kwargs) -> tuple[str, str, float]:
            try:
                res = node_label(ctx, actor, *args, **kwargs)
                res = (str(res[0]), str(res[1]), float(res[2]))
                node = actor.flows.get_node(res)
                if not node:
                    raise Exception(f"Unknown transitions {res} {actor.flows}")
            except Exception as exc:
                res = None
                logger.error(f"Exception {exc} of function {node_label}", exc_info=exc)
            return res

        return get_node_label_handler  # create wrap to get uniq key for dictionary
    elif isinstance(node_label, str):
        return (flow_label, node_label, default_transition_priority)
    elif isinstance(node_label, tuple) and len(node_label) == 2 and isinstance(node_label[-1], float):
        return (flow_label, node_label[0], node_label[-1])
    elif isinstance(node_label, tuple) and len(node_label) == 2 and isinstance(node_label[-1], str):
        return (node_label[0], node_label[-1], default_transition_priority)
    elif isinstance(node_label, tuple) and len(node_label) == 3:
        return (node_label[0], node_label[1], node_label[2])
    raise NotImplementedError(f"Unexpected node label {node_label}")


@validate_arguments
def normalize_conditions(conditions: ConditionType, reduce_function=any) -> Callable:
    if isinstance(conditions, Callable):

        @validate_arguments
        def callable_condition_handler(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
            try:
                return conditions(ctx, actor, *args, **kwargs)
            except Exception as exc:
                logger.error(f"Exception {exc} of function {conditions}", exc_info=exc)

        return callable_condition_handler
    elif isinstance(conditions, Pattern):

        @validate_arguments
        def regexp_condition_handler(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
            request = ctx.last_request
            try:
                return bool(conditions.search(request))
            except Exception as exc:
                logger.error(f"Exception {exc} for {request=}", exc_info=exc)

        return regexp_condition_handler
    elif isinstance(conditions, str):

        @validate_arguments
        def str_condition_handler(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
            request = ctx.last_request
            try:
                return conditions in request
            except Exception as exc:
                logger.error(f"Exception {exc} for {request=}", exc_info=exc)

        return str_condition_handler
    elif isinstance(conditions, list):

        function_expression_indexes = [
            index
            for index, (func, args) in enumerate(zip(conditions, conditions[1:]))
            if func in [any, all] and (isinstance(args, list) or isinstance(args, tuple))
        ]
        if function_expression_indexes:

            def reduce_func(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
                # function closure
                local_conditions = conditions[:]
                local_function_expression_indexes = function_expression_indexes[:]
                local_reduce_function = reduce_function

                # apply reduced functions
                reduced_bools = []
                for start_func_index in local_function_expression_indexes:
                    # get sub conditions
                    sub_reduce_function = local_conditions[start_func_index]
                    sub_conditions = local_conditions[start_func_index + 1]
                    # drop reduced items of local_conditions
                    local_conditions[start_func_index : start_func_index + 2] = []

                    normalized_condition = normalize_conditions(sub_conditions, sub_reduce_function)
                    reduced_bools += [normalized_condition(ctx, actor, *args, **kwargs)]
                unreduced_conditions = [normalize_conditions(cond) for cond in local_conditions]
                # apply unreduced functions
                unreduced_bools = [cond(ctx, actor, *args, **kwargs) for cond in unreduced_conditions]

                bools = unreduced_bools + reduced_bools
                return local_reduce_function(bools)

            return reduce_func
        else:

            @validate_arguments
            def iterable_condition_handler(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
                bools = [normalize_conditions(cond)(ctx, actor, *args, **kwargs) for cond in conditions]
                return reduce_function(bools)

            return iterable_condition_handler
    raise NotImplementedError(f"Unexpected conditions {conditions}")


@validate_arguments
def normalize_response(response: Any) -> Callable:
    if isinstance(response, Callable):
        return response
    else:

        @validate_arguments
        def response_handler(ctx: Context, actor: Actor, *args, **kwargs):
            return response

        return response_handler


# TODO: add exeption handling for processing
@validate_arguments
def normalize_processing(processing: Optional[Union[Callable, conlist(Callable, min_items=1)]]) -> Callable:
    if isinstance(processing, Callable):
        return processing
    elif isinstance(processing, list):

        @validate_arguments
        def list_processing_handler(
            node_label: NodeLabelTupledType, node: Node, ctx: Context, actor: Actor, *args, **kwargs
        ) -> Optional[tuple[str, Node]]:
            for proc in processing:
                node_label, node = proc(node_label, node, ctx, actor, *args, **kwargs)
            return node_label, node

        return list_processing_handler
    elif processing is None:

        @validate_arguments
        def none_handler(
            node_label: NodeLabelTupledType, node: Node, ctx: Context, actor: Actor, *args, **kwargs
        ) -> Optional[tuple[str, Node]]:
            return node_label, node

        return none_handler
    raise NotImplementedError(f"Unexpected processing {processing}")
