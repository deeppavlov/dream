import asyncio
import logging
from collections import defaultdict
from os import getenv
from signal import signal, SIGPIPE, SIG_DFL
from typing import Any, Callable, Dict, List

import aiohttp
import sentry_sdk
from sentry_sdk.integrations.aiohttp import AioHttpIntegration

from core.transport.base import ServiceGatewayConnectorBase

signal(SIGPIPE, SIG_DFL)

sentry_sdk.init(dsn=getenv("SENTRY_DSN"), integrations=[AioHttpIntegration()])
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


class HTTPConnector:
    def __init__(self, session: aiohttp.ClientSession, url: str):
        self.session = session
        self.url = url

    async def send(self, payload: Dict, callback: Callable):
        try:
            async with self.session.post(self.url, json=payload["payload"]) as resp:
                resp.raise_for_status()
                response = await resp.json()
            await callback(task_id=payload["task_id"], response=response[0])
        except Exception as e:
            response = e
            await callback(task_id=payload["task_id"], response=response)


class AioQueueConnector:
    def __init__(self, queue):
        self.queue = queue

    async def send(self, payload: Dict, **kwargs):
        await self.queue.put(payload)


class QueueListenerBatchifyer:
    def __init__(self, session, url, queue, batch_size):
        self.session = session
        self.url = url
        self.queue = queue
        self.batch_size = batch_size

    async def call_service(self, process_callable):
        while True:
            batch = []
            rest = self.queue.qsize()
            for _ in range(min(self.batch_size, rest)):
                item = await self.queue.get()
                batch.append(item)
            if batch:
                model_payload = self.glue_tasks(batch)
                async with self.session.post(self.url, json=model_payload) as resp:
                    response = await resp.json()
                for task, task_response in zip(batch, response):
                    asyncio.create_task(process_callable(task_id=task["task_id"], response=task_response))
            await asyncio.sleep(0.1)

    def glue_tasks(self, batch):
        if len(batch) == 1:
            return batch[0]["payload"]
        else:
            result = {k: [] for k in batch[0]["payload"].keys()}
            for el in batch:
                for k in result.keys():
                    result[k].extend(el["payload"][k])
            return result


class ConfidenceResponseSelectorConnector:
    async def send(self, payload: Dict, callback: Callable):
        response = payload["payload"]["hypotheses"]
        best_skill = sorted(response, key=lambda x: x["confidence"], reverse=True)[0]
        await callback(task_id=payload["task_id"], response=best_skill)


class EventSetOutputConnector:
    def __init__(self, service_name: str):
        self.service_name = service_name

    async def send(self, payload, callback: Callable):
        event = payload["payload"].get("event", None)
        if not event or not isinstance(event, asyncio.Event):
            raise ValueError("'event' key is not presented in payload")
        await callback(task_id=payload["task_id"], response=" ")
        event.set()


class AgentGatewayToChannelConnector:
    pass


class AgentGatewayToServiceConnector:
    _to_service_callback: Callable
    _service_name: str

    def __init__(self, to_service_callback: Callable, service_name: str):
        self._to_service_callback = to_service_callback
        self._service_name = service_name

    async def send(self, payload: Dict, **_kwargs):
        await self._to_service_callback(payload=payload, service_name=self._service_name)


class ServiceGatewayHTTPConnector(ServiceGatewayConnectorBase):
    _session: aiohttp.ClientSession
    _url: str
    _service_name: str

    def __init__(self, service_config: Dict) -> None:
        super().__init__(service_config)
        self._session = aiohttp.ClientSession()
        self._service_name = service_config["name"]
        self._url = service_config["url"]

    async def send_to_service(self, payloads: List[Dict]) -> List[Any]:
        batch = defaultdict(list)
        for payload in payloads:
            for key, value in payload.items():
                batch[key].extend(value)
        async with await self._session.post(self._url, json=batch) as resp:
            responses_batch = await resp.json()

        return responses_batch


class PredefinedTextConnector:
    def __init__(self, response_text, annotations=None):
        self.response_text = response_text
        self.annotations = annotations or {}

    async def send(self, payload: Dict, callback: Callable):
        await callback(
            task_id=payload["task_id"], response={"text": self.response_text, "annotations": self.annotations}
        )
