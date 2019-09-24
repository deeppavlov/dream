import asyncio
import aiohttp
from typing import Dict, List, Callable


class HTTPConnector:
    def __init__(self, session: aiohttp.ClientSession, url: str, formatter: Callable, service_name: str):
        self.session = session
        self.url = url
        self.formatter = formatter
        self.service_name = service_name

    async def send(self, payload: Dict):
        async with self.session.post(self.url, json=self.formatter([payload])) as resp:
            response = await resp.json()
            return {self.service_name: self.formatter(response[0], mode='out')}


class AioQueueConnector:
    def __init__(self, queue):
        self.queue = queue

    async def send(self, payload: Dict):
        await self.queue.put(payload)


class QueueListenerBatchifyer:
    def __init__(self, session, url, formatter, service_name, queue, batch_size):
        self.session = session
        self.url = url
        self.formatter = formatter
        self.service_name = service_name
        self.queue = queue
        self.batch_size = batch_size

    async def call_service(self, process_callable):
        while True:
            batch = []
            rest = self.queue.qsize()
            for i in range(min(self.batch_size, rest)):
                item = await self.queue.get()
                batch.append(item)
            if batch:
                tasks = []
                async with self.session.post(self.url, json=self.formatter(batch)) as resp:
                    response = await resp.json()
                for dialog, response_text in zip(batch, response):
                    tasks.append(process_callable(dialog['id'], self.service_name,
                                                  {self.service_name: self.formatter(response_text, mode='out')}))
                await asyncio.gather(*tasks)
            await asyncio.sleep(0.1)


class ConfidenceResponseSelectorConnector:
    async def send(self, payload: Dict):
        response = payload['utterances'][-1]['selected_skills']
        skill_name = sorted(response.items(), key=lambda x: x[1]['confidence'], reverse=True)[0][0]
        return {'confidence_response_selector': skill_name}


class HttpOutputConnector:
    def __init__(self, intermediate_storage: Dict):
        self.intermediate_storage = intermediate_storage

    async def send(self, payload):
        message_uuid = payload['message_uuid']
        event = payload['event']
        response_text = payload['dialog']['utterances'][-1]['text']
        self.intermediate_storage[message_uuid] = response_text
        event.set()


class EventSetOutputConnector:
    async def send(self, payload):
        event = payload.get('event', None)
        if not event or not isinstance(event, asyncio.Event):
            raise ValueError("'event' key is not presented in payload")
        event.set()
