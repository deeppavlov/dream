from datetime import datetime
import uuid
import argparse
from random import choice

import asyncio

from core.agent import Agent
from core.state_manager import StateManager
from core.pipeline import Pipeline
from core.service import Service
from core.config_parser import parse_old_config
from core.connectors import EventSetOutputConnector

import logging

logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(logging.WARNING)

parser = argparse.ArgumentParser()
parser.add_argument('phrasefile', help='name of the file with phrases for dialog', type=str,
                    default="../utils/ru_test_phrases.txt")


def init_agent():
    services, workers, session, _ = parse_old_config()
    endpoint = Service('cmd_responder', EventSetOutputConnector('cmd_responder').send,
                       StateManager.save_dialog_dict, 1, ['responder'])
    input_srv = Service('input', None, StateManager.add_human_utterance_simple_dict, 1, ['input'])
    pipeline = Pipeline(services)
    pipeline.add_responder_service(endpoint)
    pipeline.add_input_service(input_srv)
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
        tasks.append(agent.register_msg(utterance=u, user_telegram_id=u_tg_id, user_device_type=u_d_type,
                                        location=loc, channel_type=ch_t, require_response=True))
    res = await asyncio.gather(*tasks, return_exceptions=False)

    await session.close()

    return [i['dialog']['utterances'][-1]['text'] for i in res]


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(main())
    print(result)
