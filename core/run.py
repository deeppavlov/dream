import asyncio
import aiohttp

from datetime import datetime
from core.agent import AsyncAgent
from core.pipeline import Pipeline, Service, simple_workflow_formatter
from core.connectors import CmdConnector
from core.config_parser import services, worker_tasks, session
from core.state_manager import StateManager
from core.transform_config import DEBUG

endpoint = Service('cmd_responder', CmdConnector(), None, 1, ['responder'], set(), simple_workflow_formatter)


def prepare_agent():
    pipeline = Pipeline(services)
    pipeline.add_responder_service(endpoint)

    agent = AsyncAgent(pipeline, StateManager)

    return agent.register_msg


async def run():
    register_func = prepare_agent()
    user_id = input('Provide user id: ')
    while True:
        msg = input(f'You ({user_id}): ').strip()
        if msg:
            await register_func(msg, user_id, 'cmd', datetime.now(), 'lab', 'cmd_client')


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.set_debug(DEBUG)
    future = asyncio.ensure_future(run())
    try:
        loop.run_until_complete(future)
    except Exception as e:
        raise e
    finally:
        loop.run_until_complete(asyncio.gather(session.close()))
        loop.stop()
        loop.close()
