import logging
from uuid import UUID, uuid4

from typing import ForwardRef
from typing import Any, Optional, Union

from pydantic import BaseModel, validate_arguments, Field, validator


logger = logging.getLogger(__name__)

Context = ForwardRef("Context")


@validate_arguments
def sort_dict_keys(dictionary: dict) -> dict:
    return {key: dictionary[key] for key in sorted(dictionary)}


class Context(BaseModel):
    id: Union[UUID, int, str] = Field(default_factory=uuid4)
    node_labels: dict[int, tuple[str, str]] = {}
    requests: dict[int, Any] = {}
    responses: dict[int, Any] = {}
    previous_index: int = -1
    current_index: int = -1
    misc: dict[str, Any] = {}
    validation: bool = False

    # validators
    _sort_node_labels = validator("node_labels", allow_reuse=True)(sort_dict_keys)
    _sort_requests = validator("requests", allow_reuse=True)(sort_dict_keys)
    _sort_responses = validator("responses", allow_reuse=True)(sort_dict_keys)

    @classmethod
    def cast(
        cls,
        ctx: Union[Context, dict, str] = {},
        *args,
        **kwargs,
    ) -> Union[Context, dict, str]:
        if not ctx:
            ctx = Context()
        elif isinstance(ctx, dict):
            ctx = Context.parse_obj(ctx)
        elif isinstance(ctx, str):
            ctx = Context.parse_raw(ctx)
        elif not issubclass(type(ctx), Context):
            raise ValueError(
                f"context expected as sub class of Context class or object of dict/str(json) type, but got {ctx}"
            )
        return ctx

    @validate_arguments
    def add_request(
        self,
        request: Any,
        current_index: Optional[int] = None,
    ):
        if current_index is None:
            self.current_index += 1
        else:
            self.current_index = current_index

        self.requests[self.current_index] = request

    @validate_arguments
    def add_response(self, response: Any):
        self.responses[self.current_index] = response

    @validate_arguments
    def add_node_label(self, node_label: tuple[str, str]):
        self.previous_index = self.current_index
        self.node_labels[self.current_index] = node_label

    @validate_arguments
    def clear(self, hold_last_n_indexes: int, field_names: list[str] = ["requests", "responses", "node_labels"]):
        if "requests" in field_names:
            for index in list(self.requests.keys())[:-hold_last_n_indexes]:
                del self.requests[index]
        if "responses" in field_names:
            for index in list(self.responses.keys())[:-hold_last_n_indexes]:
                del self.responses[index]
        if "mics" in field_names:
            self.misc.clear()
        if "node_labels" in field_names:
            for index in list(self.node_labels.keys())[:-hold_last_n_indexes]:
                del self.node_labels[index]

    @property
    def previous_node_label(self) -> Optional[tuple[str, str]]:
        return self.node_labels.get(self.previous_index)

    @property
    def last_response(self) -> Optional[Any]:
        vals = list(self.responses.values())[-1:]
        if vals:
            return vals[0]

    @property
    def last_request(self) -> Optional[Any]:
        vals = list(self.requests.values())[-1:]
        if vals:
            return vals[0]


Context.update_forward_refs()
