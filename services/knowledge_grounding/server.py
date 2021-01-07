import logging
import os
import random
import time

import sentry_sdk
import torch
from flask import Flask, request, jsonify
from parlai.core.params import ParlaiParser
from parlai.core.agents import create_agent
from parlai.core.worlds import create_task
from parlai.core.script import ParlaiScript, register_script
from parlai.agents.courier.courier import CourierAgent
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(dsn=os.getenv('SENTRY_DSN'), integrations=[FlaskIntegration()])


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


cuda = torch.cuda.is_available()
if cuda:
    torch.cuda.set_device(0)  # singe gpu
    device = torch.device('cuda')
else:
    device = torch.device('cpu')

logger.info(f'knowledge grounding is set to run on {device}')


logger.info('knowledge grounding script is preparing...')


@register_script('get model response')
class GetModelResponse(ParlaiScript):
    @classmethod
    def setup_args(cls):
        parser = ParlaiParser(True, True, 'Get response from model in knowledge grounded conversation')
        parser.add_argument(
            '-it',
            '--interactive-task',
            type='bool',
            default=True,
            help='Create interactive version of task',
        )
        parser.add_argument(
            '--user-input-topic',
            type=str,
            default='',
            help='User input topic',
        )
        parser.add_argument(
            '--user-input-knowledge',
            type=str,
            default='',
            help='User input knowledge',
        )
        parser.add_argument(
            '--user-input-text',
            type=str,
            default='',
            help='User input text',
        )
        parser.add_argument(
            '--user-input-history',
            type=str,
            default='',
            help='User input history',
        )
        parser.set_defaults(interactive_mode=True, task='interactive')
        return parser

    def run(self):
        opt = self.opt
        if isinstance(self.opt, ParlaiParser):
            logging.error('opt should be passed, not Parser')
            opt = self.opt.parse_args()
        # Create model and courier and assign them to the specified task
        agent = create_agent(opt, requireModelExists=True)
        courier_agent = CourierAgent(opt)
        world = create_task(opt, [courier_agent, agent])
        user_input = {
            'topic': opt['user_input_topic'],
            'knowledge': opt['user_input_knowledge'],
            'text': opt['user_input_text'],
            'history': opt['user_input_history'].split('\n') if opt['user_input_history'] else ['']
        }
        response = world.parley(user_input)
        courier_agent.finished = True
        return response['text']


try:
    GetModelResponse.main(
        task='redditgk',
        datatype='test',
        user_input_topic='',
        user_input_knowledge='.',
        user_input_text='hi',
        user_input_history='',
        split_lines=False,
        model_file='zoo:wizard_of_wikipedia/end2end_generator/model',
    )
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)

logger.info(f'knowledge grounding script is ready')

app = Flask(__name__)


@app.route("/respond", methods=['POST'])
def respond():
    batch = request.json['batch']
    responses = []
    random.seed(42)
    for sample in batch:
        response = ""
        st_time = time.time()
        if sample['knowledge']:
            try:
                response = GetModelResponse.main(
                    task='redditgk',
                    datatype='test',
                    user_input_topic=sample['topic'],
                    user_input_knowledge=sample['knowledge'],
                    user_input_text=sample['text'],
                    user_input_history=sample['history'],
                    split_lines=False,
                    model_file='zoo:wizard_of_wikipedia/end2end_generator/model',
                )
            except Exception as e:
                sentry_sdk.capture_exception(e)
                logger.exception(e)
            logger.info(f'Current sample response: {response}')
        else:
            logger.info(f'Sample knowledge is empty, returning empty response')
        total_time = time.time() - st_time
        logger.info(f'knowledge grounding: one sample from batch exec time: {total_time:.3f}s')
        responses.append(response)
    return jsonify(responses)
