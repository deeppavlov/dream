import json
import logging
import os

from core.agent import Agent
from core.connectors import EventSetOutputConnector, PredefinedTextConnector
from core.db import DataBase
from core.log import LocalResponseLogger
from core.pipeline import Pipeline
from core.service import Service
from core.state_manager import StateManager
from core.workflow_manager import WorkflowManager
from http_api.api import init_app
from parse_config import PipelineConfigParser


service_logger = logging.getLogger('service_logger')


async def app_factory():
    db_conf = os.getenv('DB_CONFIG', 'db_conf.json')
    pipeline_conf = os.getenv('PIPELINE_CONFIG', 'pipeline_conf.json')
    time_limit = int(os.getenv('TIME_LIMIT', '4'))

    with open(db_conf, 'r') as db_config:
        db_data = json.load(db_config)

    if db_data.pop('env', False):
        for k, v in db_data.items():
            db_data[k] = os.getenv(v)

    db = DataBase(**db_data)

    sm = StateManager(db.get_db())

    with open(pipeline_conf, 'r') as pipeline_config:
        pipeline_data = json.load(pipeline_config)

    pipeline_config = PipelineConfigParser(sm, pipeline_data)

    input_srv = Service('input', None, sm.add_human_utterance, 1, ['input'])
    responder_srv = Service('responder', EventSetOutputConnector('responder').send,
                            sm.save_dialog, 1, ['responder'])

    last_chance_srv = pipeline_config.last_chance_service or Service(
        'last_chance', PredefinedTextConnector('Sorry, something went wrong.').send,
        sm.add_bot_utterance_last_chance, 1, ['last_chance'])
    timeout_srv = pipeline_config.timeout_service or Service(
        'timeout', PredefinedTextConnector("Sorry, I need to think more on that.").send,
        sm.add_bot_utterance_last_chance, 1, ['timeout'])

    pipeline = Pipeline(pipeline_config.services, input_srv, responder_srv, last_chance_srv, timeout_srv)

    response_logger = LocalResponseLogger(True)
    agent = Agent(pipeline, sm, WorkflowManager(), response_logger=response_logger)

    app = await init_app(
        agent, pipeline_config.session, pipeline_config.workers,
        response_logger, True, time_limit
    )

    return app
