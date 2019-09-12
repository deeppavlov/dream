import asyncio
import aiohttp
from typing import Dict, List


class HTTPConnector:
    def __init__(self, session, url, formatter, service_name):
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


class CmdOutputConnector:
    async def send(self, payload):
        print('bot: ', payload['utterances'][-1]['text'])


class HttpOutputConnector:
    def __init__(self, intermediate_storage: Dict):
        self.intermediate_storage = intermediate_storage

    async def send(self, payload):
        message_uuid = payload['message_uuid']
        event = payload['event']
        response_text = payload['dialog'].utterances[-1].text
        self.intermediate_storage[message_uuid] = response_text
        event.set()


class ConfidenceResponseSelectorConnector:
    async def send(self, payload: Dict):
        skill_name = ''
        response = payload['utterances'][-1]['selected_skills']
        skill_name = sorted(response.items(), key=lambda x: x[1]['confidence'], reverse=True)[0][0]
        return {'confidence_response_selector': skill_name}


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
