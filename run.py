import argparse
import json
import logging
import os

import yaml
from aiohttp import web

from core.agent import Agent
from core.cmd_client import run_cmd
from core.connectors import EventSetOutputConnector
from core.db import DataBase
from http_api.api import init_app
from core.log import LocalResponseLogger
from core.pipeline import Pipeline
from core.service import Service
from core.state_manager import StateManager
from core.workflow_manager import WorkflowManager
from parse_config import PipelineConfigParser

service_logger = logging.getLogger('service_logger')

parser = argparse.ArgumentParser()
parser.add_argument('-pl', '--pipeline_config', help='service name for service run mode', type=str,
                    default='pipeline_conf.json')
parser.add_argument('-db', '--db_config', help='service name for service run mode', type=str, default='db_conf.json')
parser.add_argument("-ch", "--channel", help="run agent in telegram, cmd_client or http_client", type=str,
                    choices=['cmd_client', 'http_client', 'telegram'], default='cmd_client')
parser.add_argument('-p', '--port', help='port for http client, default 4242', default=4242)
parser.add_argument("-px", "--proxy", help="proxy for telegram client", type=str, default='')
parser.add_argument('-t', '--token', help='token for telegram client', type=str)

parser.add_argument('-rl', '--response_logger', help='run agent with services response logging', action='store_true')
parser.add_argument('-d', '--debug', help='run in debug mode', action='store_true')
args = parser.parse_args()


def main():
    with open(args.db_config, 'r') as db_config:
        if args.db_config.endswith('.json'):
            db_data = json.load(db_config)
        elif args.db_config.endswith('.yml'):
            db_data = yaml.load(db_config)
        else:
            raise ValueError('unknown format for db_config')

    if db_data.pop('env', False):
        for k, v in db_data.items():
            db_data[k] = os.getenv(v)

    db = DataBase(**db_data)

    sm = StateManager(db.get_db())

    with open(args.pipeline_config, 'r') as pipeline_config:
        if args.pipeline_config.endswith('.json'):
            pipeline_data = json.load(pipeline_config)
        elif args.pipeline_config.endswith('.yml'):
            pipeline_data = yaml.load(pipeline_config)
        else:
            raise ValueError('unknown format for pipeline_config')
    pipeline_config = PipelineConfigParser(sm, pipeline_data)

    input_srv = Service('input', None, sm.add_human_utterance, 1, ['input'])
    endpoint_srv = Service('responder', EventSetOutputConnector('responder').send,
                           sm.save_dialog, 1, ['responder'])

    pipeline = Pipeline(pipeline_config.services)
    pipeline.add_responder_service(endpoint_srv)
    pipeline.add_input_service(input_srv)

    response_logger = LocalResponseLogger(args.response_logger)
    agent = Agent(pipeline, sm, WorkflowManager(), response_logger=response_logger)
    if pipeline_config.gateway:
        pipeline_config.gateway.on_channel_callback = agent.register_msg
        pipeline_config.gateway.on_service_callback = agent.process
    try:
        if args.channel == 'cmd_client':
            run_cmd(agent, pipeline_config.session, pipeline_config.workers, args.debug)

        elif args.channel == 'http_client':
            app = init_app(agent, pipeline_config.session, pipeline_config.workers, response_logger, args.debug)
            web.run_app(app, port=args.port)
    except Exception as e:
        raise e
    finally:
        logging.shutdown()


if __name__ == '__main__':
    main()
