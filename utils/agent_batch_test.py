from datetime import datetime
import uuid
import argparse
from random import choice

import asyncio

from core.agent import Agent
from core.state_manager import StateManager
from core.pipeline import Pipeline, Service
from core.config_parser import parse_old_config
from core.connectors import EventSetOutputConnector

import logging

logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(logging.WARNING)

parser = argparse.ArgumentParser()
parser.add_argument('phrasefile', help='name of the file with phrases for dialog', type=str,
                    default="../utils/ru_test_phrases.txt")


def init_agent():
    services, workers, session = parse_old_config()
    pipeline = Pipeline(services)
    endpoint = Service('http_responder', EventSetOutputConnector(), None, 1, ['responder'])
    pipeline.add_responder_service(endpoint)
    agent = Agent(pipeline, StateManager())
    return agent, session


async def main():
    args = parser.parse_args()
    with open(args.phrasefile, 'r') as file:
        phrases = [line.rstrip('\n') for line in file]
        length = len(phrases)

    u_d_types = [choice(['iphone', 'android']) for _ in range(length)]
    date_times = [datetime.utcnow()] * length
    locations = [choice(['moscow', 'novosibirsk', 'novokuznetsk']) for _ in range(length)]
    ch_types = ['cmd_client'] * length
    agent, session = init_agent()
    tasks = []
    for u, u_d_type, dt, loc, ch_t in zip(phrases, u_d_types, date_times, locations, ch_types):
        u_tg_id = uuid.uuid4().hex
        tasks.append(agent.register_msg(u, u_tg_id, u_d_type, dt, loc, ch_t, None, True))
    res = await asyncio.gather(*tasks, return_exceptions=False)

    await session.close()

    return [i['dialog'].utterances[-1].text for i in res]


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(main())
    print(result)
