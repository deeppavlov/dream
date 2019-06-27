import argparse
import time
from datetime import datetime
from threading import Thread
from multiprocessing import Process, Pipe
from multiprocessing.connection import Connection
from typing import Callable, Optional, Collection, Hashable, List, Tuple

import telebot
from telebot.types import Message, Location, User

from core.config import TELEGRAM_TOKEN, TELEGRAM_PROXY


parser = argparse.ArgumentParser()
parser.add_argument("-ch", "--channel", help="run agent in telegram or cmd_client", type=str,
                    choices=['telegram', 'cmd_client'], default='cmd_client')
args = parser.parse_args()
CHANNEL = args.channel


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


def experimental_bot(
        model_function: Callable[
            ..., Callable[[Collection[Message], Collection[Hashable]], Collection[str]]],
        token: str, proxy: Optional[str] = None, *, batch_size: int = -1, poll_period: float = 0.5):
    """

    Args:
        model_function: a function that produces an agent
        token: telegram token string
        proxy: https or socks5 proxy string for telebot
        batch_size: maximum batch size for the model
        poll_period: how long to wait every time no input was done for the model

    Returns: None

    """
    if proxy is not None:
        telebot.apihelper.proxy = {'https': proxy}

    bot = telebot.TeleBot(token)

    parent_conn, child_conn = Pipe()
    p = Process(target=_model_process, args=(model_function, child_conn),
                kwargs={'batch_size': batch_size, 'poll_period': poll_period})
    p.start()

    def responder():
        while True:
            text, chat_id = parent_conn.recv()
            bot.send_message(chat_id, text)

    t = Thread(target=responder)
    t.start()

    @bot.message_handler()
    def handle_message(message: Message):
        parent_conn.send((message, message.chat.id))

    bot.polling(none_stop=True)


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

    anno_names, anno_urls = zip(
        *[(annotator['name'], annotator['url']) for annotator in ANNOTATORS])
    preprocessor = Service(
        rest_caller=RestCaller(max_workers=MAX_WORKERS, names=anno_names, urls=anno_urls))
    postprocessor = DefaultPostprocessor()
    skill_caller = RestCaller(max_workers=MAX_WORKERS)
    response_selector = ConfidenceResponseSelector()
    skill_selector = None
    if SKILL_SELECTORS:
        ss_names, ss_urls = zip(*[(selector['name'], selector['url']) for selector in SKILL_SELECTORS])
        skill_selector = ChitchatQASelector(
            rest_caller=RestCaller(max_workers=MAX_WORKERS, names=ss_names, urls=ss_urls))
    skill_manager = SkillManager(skill_selector=skill_selector, response_selector=response_selector,
                                 skill_caller=skill_caller, profile_handlers=[skill['name'] for skill in SKILLS
                                                                              if skill.get('profile_handler')])

    agent = Agent(state_manager, preprocessor, postprocessor, skill_manager)

    def infer_telegram(messages: Collection[Message], dialog_ids):
        utterances: List[Optional[str]] = [message.text for message in messages]
        tg_users: List[User] = [message.from_user for message in messages]

        u_tg_ids = [str(user.id) for user in tg_users]
        u_tg_data = [{
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name
        }
            for user in tg_users]

        u_d_types = [None] * len(messages)
        date_times = [datetime.utcnow()] * len(messages)
        locations: List[Optional[Location]] = [message.location for message in messages]
        ch_types = ['telegram'] * len(messages)

        answers = agent(utterances=utterances, user_telegram_ids=u_tg_ids, user_device_types=u_d_types,
                        date_times=date_times, locations=locations, channel_types=ch_types)
        return answers

    def infer_cmd(messages, dialog_ids):
        utterances: List[Optional[str]] = [message['data'] for message in messages]
        u_ids = [str(message['from_user']['id']) for message in messages]

        date_times = [datetime.utcnow()] * len(messages)
        locations: List[Optional[Location]] = [None] * len(messages)

        answers = agent(utterances=utterances, user_telegram_ids=u_ids, user_device_types=[None] * len(messages),
                        date_times=date_times, locations=locations, channel_types=['cmd_client'] * len(messages))
        return answers

    if CHANNEL == 'telegram':
        return infer_telegram
    else:
        return infer_cmd


def main():
    if CHANNEL == 'telegram':
        experimental_bot(run, token=TELEGRAM_TOKEN, proxy=TELEGRAM_PROXY)
    else:
        message_processor = run()
        user_id = input('Provide user id: ')
        user = {'id': user_id}
        while True:
            msg = input(f'You ({user_id}): ').strip()
            if msg:
                message = {'data': msg, 'from_user': user}
                responses = message_processor([message], [1])
                print('Bot: ', responses[0])


if __name__ == '__main__':
    main()
