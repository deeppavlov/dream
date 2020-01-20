from typing import List, Callable, TypeVar, Dict, Any, Optional


class AgentGatewayBase:
    _on_service_callback: Optional[Callable]
    _on_channel_callback: Optional[Callable]

    def __init__(self, on_service_callback: Optional[Callable] = None,
                 on_channel_callback: Optional[Callable] = None, *args, **kwargs):

        super(AgentGatewayBase, self).__init__(*args, **kwargs)
        self._on_service_callback = on_service_callback
        self._on_channel_callback = on_channel_callback

    @property
    def on_service_callback(self):
        return self._on_service_callback

    @on_service_callback.setter
    def on_service_callback(self, callback: Callable):
        self._on_service_callback = callback

    @property
    def on_channel_callback(self):
        return self._on_channel_callback

    @on_channel_callback.setter
    def on_channel_callback(self, callback: Callable):
        self._on_channel_callback = callback

    async def send_to_service(self, service: str, dialog: Dict) -> None:
        raise NotImplementedError

    async def send_to_channel(self, channel_id: str, user_id: str, response: str) -> None:
        raise NotImplementedError


class ServiceGatewayConnectorBase:
    _service_config: dict

    def __init__(self, service_config: Dict) -> None:
        self._service_config = service_config

    async def send_to_service(self, dialogs: List[Dict]) -> List[Any]:
        raise NotImplementedError


class ServiceGatewayBase:
    _to_service_callback: Callable

    def __init__(self, to_service_callback: Callable, *args, **kwargs) -> None:
        super(ServiceGatewayBase, self).__init__(*args, **kwargs)
        self._to_service_callback = to_service_callback


class ChannelGatewayConnectorBase:
    _config: dict
    _channel_id: str
    _on_channel_callback: Callable

    def __init__(self, config: Dict, on_channel_callback: Callable) -> None:
        self._config = config
        self._channel_id = self._config['channel']['id']
        self._on_channel_callback = on_channel_callback

    async def send_to_channel(self, user_id: str, response: str) -> None:
        raise NotImplementedError


class ChannelGatewayBase:
    _to_channel_callback: Callable

    def __init__(self, to_channel_callback: Callable, *args, **kwargs) -> None:
        super(ChannelGatewayBase, self).__init__(*args, **kwargs)
        self._to_channel_callback = to_channel_callback

    async def send_to_agent(self, utterance: str, channel_id: str, user_id: str, reset_dialog: bool) -> None:
        raise NotImplementedError


TAgentGateway = TypeVar('TAgentGateway', bound=AgentGatewayBase)
TServiceGatewayConnectorBase = TypeVar('TServiceGatewayConnectorBase', bound=ServiceGatewayConnectorBase)
TServiceGateway = TypeVar('TServiceGateway', bound=ServiceGatewayBase)
TChannelGatewayConnectorBase = TypeVar('TChannelGatewayConnectorBase', bound=ChannelGatewayConnectorBase)
TChannelGateway = TypeVar('TChannelGateway', bound=ChannelGatewayBase)
