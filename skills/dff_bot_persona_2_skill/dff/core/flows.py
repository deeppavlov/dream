import logging
from typing import Union, Callable, Optional, Any


from pydantic import BaseModel, conlist, validator, validate_arguments, Extra

from .normalization import NodeLabelType, ConditionType
from .normalization import normalize_node_label, normalize_conditions, normalize_response, normalize_processing

logger = logging.getLogger(__name__)
# TODO: add texts


class Transition(BaseModel, extra=Extra.forbid):
    @validate_arguments
    def get_transitions(
        self, flow_label: str, default_transition_priority: float, global_transition_flag=False
    ) -> dict[Union[Callable, tuple[str, str, float]], Callable]:
        transitions = {}
        gtrs = self.global_transitions if hasattr(self, "global_transitions") else {}
        trs = self.transitions if hasattr(self, "transitions") else {}
        items = gtrs if global_transition_flag else trs
        for node_label in items:
            normalized_node_label = normalize_node_label(node_label, flow_label, default_transition_priority)
            normalized_conditions = normalize_conditions(items[node_label])
            transitions[normalized_node_label] = normalized_conditions
        return transitions


class Node(Transition):
    transitions: dict[NodeLabelType, ConditionType] = {}
    response: Union[Any, Callable]
    processing: Union[Callable, conlist(Callable, min_items=1)] = None
    misc: Optional[Any] = None

    def get_response(self):
        return normalize_response(self.response)

    def get_processing(self):
        return normalize_processing(self.processing)


class Flow(Transition):
    global_transitions: dict[NodeLabelType, ConditionType] = {}
    graph: dict[str, Node] = {}

    @validate_arguments
    def get_transitions(
        self, flow_label: str, default_transition_priority: float, global_transition_flag=False
    ) -> dict[Union[Callable, tuple[str, str, float]], Callable]:
        transitions = super(Flow, self).get_transitions(flow_label, default_transition_priority, global_transition_flag)
        for node in self.graph.values():
            transitions |= node.get_transitions(flow_label, default_transition_priority, global_transition_flag)
        return transitions


def error_handler(error_msgs: list, msg: str, exception: Optional[Exception] = None, logging_flag: bool = True):
    error_msgs.append(msg)
    logging_flag and logger.error(msg, exc_info=exception)


class Flows(BaseModel, extra=Extra.forbid):
    flows: dict[str, Flow]

    @validator("flows")
    def is_not_empty(cls, fields: dict) -> dict:
        if not any(fields.values()):
            raise ValueError("expected not empty flows")
        return fields

    @validate_arguments
    def get_transitions(
        self, default_transition_priority: float, global_transition_flag=False
    ) -> dict[Union[Callable, tuple[str, str, float]], Callable]:
        transitions = {}
        for flow_label, node in self.flows.items():
            transitions |= node.get_transitions(flow_label, default_transition_priority, global_transition_flag)
        return transitions

    @validate_arguments
    def get_node(self, node_label: NodeLabelType, flow_label: str = "") -> Optional[Node]:
        normalized_node_label = normalize_node_label(node_label, flow_label, -1)
        flow_label = normalized_node_label[0]
        node_label = normalized_node_label[1]
        node = self.flows.get(flow_label, Flow()).graph.get(node_label)
        if node is None:
            logger.warn(f"Unknown pair(flow_label:node_label) = {flow_label}:{node_label}")
        return node

    def __getitem__(self, k):
        return self.flows[k]

    def get(self, k, item=None):
        return self.flows.get(k, item)

    def keys(self):
        return self.flows.keys()

    def items(self):
        return self.flows.items()

    def values(self):
        return self.flows.values()

    def __iter__(self):
        return self.flows
