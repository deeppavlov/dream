from typing import Any, Dict, TypeVar


class MessageBase:
    agent_name: str
    msg_type: str

    def __init__(self, msg_type: str, agent_name: str):
        self.msg_type = msg_type
        self.agent_name = agent_name

    @classmethod
    def from_json(cls, message_json):
        return cls(**message_json)

    def to_json(self) -> dict:
        return self.__dict__


TMessageBase = TypeVar('TMessageBase', bound=MessageBase)


class ServiceTaskMessage(MessageBase):
    payload: Dict

    def __init__(self, agent_name: str, payload: Dict) -> None:
        super().__init__('service_task', agent_name)
        self.payload = payload


class ServiceResponseMessage(MessageBase):
    response: Any
    task_id: str

    def __init__(self, task_id: str, agent_name: str, response: Any) -> None:
        super().__init__('service_response', agent_name)
        self.task_id = task_id
        self.response = response


class ServiceErrorMessage(MessageBase):
    formatted_exc: str

    def __init__(self, task_id: str, agent_name: str, formatted_exc: str) -> None:
        super().__init__('error', agent_name)
        self.task_id = task_id
        self.formatted_exc = formatted_exc

    @property
    def exception(self) -> Exception:
        return Exception(self.formatted_exc)


class ToChannelMessage(MessageBase):
    channel_id: str
    user_id: str
    response: str

    def __init__(self, agent_name: str, channel_id: str, user_id: str, response: str) -> None:
        super().__init__('to_channel_message', agent_name)
        self.channel_id = channel_id
        self.user_id = user_id
        self.response = response


class FromChannelMessage(MessageBase):
    channel_id: str
    user_id: str
    utterance: str
    reset_dialog: bool

    def __init__(self, agent_name: str, channel_id: str, user_id: str, utterance: str, reset_dialog: bool) -> None:
        super().__init__('from_channel_message', agent_name)
        self.channel_id = channel_id
        self.user_id = user_id
        self.utterance = utterance
        self.reset_dialog = reset_dialog


_message_wrappers_map = {
    'service_task': ServiceTaskMessage,
    'service_response': ServiceResponseMessage,
    'to_channel_message': ToChannelMessage,
    'from_channel_message': FromChannelMessage,
    'error': ServiceErrorMessage
}


def get_transport_message(message_json: dict) -> TMessageBase:
    message_type = message_json.pop('msg_type')

    if message_type not in _message_wrappers_map:
        raise ValueError(f'Unknown transport message type: {message_type}')

    message_wrapper_class: TMessageBase = _message_wrappers_map[message_type]

    return message_wrapper_class.from_json(message_json)
