import asyncio
import aiohttp
from typing import Dict, List

'''
class AioQueueConnector:
    def __init__(self, queue):
        self.queue = queue
        await self.queue.join()

    async def send(self, payload: Dict):
        await self.queue.put(payload)
'''

class HTTPConnector:
    def __init__(self, session, url, formatter, name):
        self.session = session
        self.url = url
        self.formatter = formatter
        self.name = name

    async def send(self, payload: Dict):
        async with self.session.post(self.url, json=self.formatter([payload])) as resp:
            response = await resp.json()
            return {self.name: self.formatter(response[0], mode='out')}


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
    """Select a single response for each dialog turn WITHOUT MAGIC METHODS.
    """
    async def send(self, payload: Dict):
        skill_name = ''
        response = payload['utterances'][-1]['selected_skills']
        skill_name = sorted(response.items(), key=lambda x: x[1]['confidence'], reverse=True)[0][0]
        return {'confidence_response_selector': skill_name}
