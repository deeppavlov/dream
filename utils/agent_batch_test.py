from datetime import datetime
import uuid
import argparse
from random import choice

import asyncio

from core.agent import Agent
from core.state_manager import StateManager
from core.pipeline import Pipeline, Service
from core.config_parser import parse_old_config
from core.connectors import HttpOutputConnector

import logging

logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(logging.WARNING)

parser = argparse.ArgumentParser()
parser.add_argument('phrasefile', help='name of the file with phrases for dialog', type=str,
                    default="../utils/ru_test_phrases.txt")


def init_agent(intermediate_storage):
    services, workers, session = parse_old_config()
    pipeline = Pipeline(services)
    endpoint = Service('http_responder', HttpOutputConnector(intermediate_storage), None, 1, ['responder'])
    pipeline.add_responder_service(endpoint)
    agent = Agent(pipeline, StateManager())
    return agent, session


class DummyOutputConnector:
    def __init__(self, intermediate_storage):
        self.intermediate_storage = intermediate_storage

    async def send(self, payload):
        self.intermediate_storage[payload['message_uuid']] = payload
        payload['event'].set()


async def process_message_return_event(agent, phrase, u_tg_id, u_d_type, date_time, location, ch_type, intermediate_storage):
    event = asyncio.Event()
    message_uuid = uuid.uuid4().hex
    await agent.register_msg(utterance=phrase, user_telegram_id=u_tg_id, user_device_type=u_d_type, date_time=date_time,
                             location=location, channel_type=ch_type, event=event, message_uuid=message_uuid)
    await event.wait()
    return intermediate_storage.pop(message_uuid)


async def main():
    args = parser.parse_args()
    with open(args.phrasefile, 'r') as file:
        phrases = [line.rstrip('\n') for line in file]
        length = len(phrases)

    u_tg_ids = [str(uuid.uuid4())] * length
    u_d_types = [choice(['iphone', 'android']) for _ in range(length)]
    date_times = [datetime.utcnow()] * length
    locations = [choice(['moscow', 'novosibirsk', 'novokuznetsk']) for _ in range(length)]
    ch_types = ['cmd_client'] * length
    intermediate_storage = {}
    agent, session = init_agent(intermediate_storage)
    result = []
    for u, u_tg_id, u_d_type, dt, loc, ch_t in zip(phrases, u_tg_ids, u_d_types, date_times, locations, ch_types):
        response = await process_message_return_event(agent, u, u_tg_id, u_d_type, dt, loc, ch_t, intermediate_storage)
        result.append(response)

    await session.close()

    return result


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(main())
    print(result)
