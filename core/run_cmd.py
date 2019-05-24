import time
from datetime import datetime
from threading import Thread
from multiprocessing import Process, Pipe
from multiprocessing.connection import Connection
from typing import Callable, Optional, Collection, Hashable, List, Tuple, Dict
from os import getenv


def _model_process(model_function: Callable, conn: Connection, batch_size: int = -1, *,
                   poll_period: float = 0.5):
    model: Callable[[Collection[str], Collection[Hashable]], Collection[str]] = model_function()
    if batch_size <= 0:
        batch_size = float('inf')

    while True:
        batch: List[Tuple[str, Hashable]] = []
        while conn.poll() and len(batch) < batch_size:
            batch.append(conn.recv())

        if not batch:
            time.sleep(poll_period)
            continue

        messages, dialog_ids = zip(*batch)
        responses = model(messages, dialog_ids)
        for response, dialog_id in zip(responses, dialog_ids):
            conn.send((response, dialog_id))


def run():
    from core.agent import Agent
    from core.state_manager import StateManager
    from core.skill_manager import SkillManager
    from core.rest_caller import RestCaller
    from core.service import Service
    from core.postprocessor import DefaultPostprocessor
    from core.response_selector import ConfidenceResponseSelector
    from core.skill_selector import ChitchatQASelector
    from core.config import MAX_WORKERS, ANNOTATORS, SKILL_SELECTORS, SKILLS

    import logging

    logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(logging.WARNING)

    state_manager = StateManager()

    anno_names, anno_urls = zip(*[(annotator['name'], annotator['url']) for annotator in ANNOTATORS])
    preprocessor = Service(
        rest_caller=RestCaller(max_workers=MAX_WORKERS, names=anno_names, urls=anno_urls))
    postprocessor = DefaultPostprocessor()
    skill_caller = RestCaller(max_workers=MAX_WORKERS)
    response_selector = ConfidenceResponseSelector()
    ss_names, ss_urls = zip(*[(annotator['name'], annotator['url']) for annotator in SKILL_SELECTORS])
    skill_selector = ChitchatQASelector(rest_caller=RestCaller(max_workers=MAX_WORKERS, names=ss_names, urls=ss_urls))
    skill_manager = SkillManager(skill_selector=skill_selector, response_selector=response_selector,
                                 skill_caller=skill_caller, profile_handlers=[skill['name'] for skill in SKILLS
                                                                              if skill.get('profile_handler')])

    agent = Agent(state_manager, preprocessor, postprocessor, skill_manager)

    def infer(messages, dialog_ids):
        utterances: List[Optional[str]] = [message['data'] for message in messages]
        u_ids = [str(message['from_user']['id']) for message in messages]

        date_times = [datetime.utcnow()] * len(messages)
        locations: List[Optional[Location]] = [None] * len(messages)

        answers = agent(utterances=utterances, user_telegram_ids=u_ids, user_device_types=[None] * len(messages),
                        date_times=date_times, locations=locations, channel_types=['cmd_client'] * len(messages))
        return answers

    return infer


message_processor = run()
user_id = input('Provide user id: ')
user = {'id': user_id}
while True:
    msg = input(f'You ({user_id}): ')
    message = {'data': msg, 'from_user': user}
    responses = message_processor([message], [1])
    print('Bot: ', responses[0])
