import argparse
import time
from os import getenv

from aiohttp import web
from datetime import datetime
from string import hexdigits
from threading import Thread
from multiprocessing import Process, Pipe
from multiprocessing.connection import Connection
from typing import Callable, Optional, Collection, Hashable, List, Tuple

import telebot
from telebot.types import Message, Location, User

parser = argparse.ArgumentParser()
parser.add_argument("-ch", "--channel", help="run agent in telegram, cmd_client or http_client", type=str,
                    choices=['telegram', 'cmd_client', 'http_client'], default='cmd_client')
parser.add_argument('-p', '--port', help='port for http client, default 4242', default=4242)
args = parser.parse_args()
CHANNEL = args.channel


def _model_process(model_function: Callable, conn: Connection, batch_size: int = -1, *,
                   poll_period: float = 0.5):
    model: Callable[[Collection[str], Collection[Hashable]], Collection[str]] = model_function()
    if batch_size <= 0:
        batch_size = float('inf')

    check_time = time.time()

    while True:
        batch: List[Tuple[str, Hashable]] = []
        while conn.poll() and len(batch) < batch_size:
            batch.append(conn.recv())
            if time.time() - check_time >= poll_period:
                break

        if not batch:
            continue

        messages, dialog_ids = zip(*batch)
        responses = model(messages, dialog_ids)
        for response, dialog_id in zip(responses, dialog_ids):
            conn.send((response, dialog_id))
        check_time = time.time()  # maybe it should be moved before model call


def experimental_bot(
        model_function: Callable[
            ..., Callable[[Collection[Message], Collection[Hashable]], Collection[str]]], *,
        batch_size: int = -1, poll_period: float = 0.5):
    """

    Args:
        model_function: a function that produces an agent
        token: telegram token string
        proxy: https or socks5 proxy string for telebot
        batch_size: maximum batch size for the model
        poll_period: how long to wait every time no input was done for the model

    Returns: None

    """

    token = getenv('TELEGRAM_TOKEN')
    proxy = getenv('TELEGRAM_PROXY')

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
    from models.postprocessor import DefaultPostprocessor
    from models.response_selector import ConfidenceResponseSelector
    from core.transform_config import MAX_WORKERS, ANNOTATORS, SKILL_SELECTORS, SKILLS, RESPONSE_SELECTORS

    import logging

    logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(logging.WARNING)

    state_manager = StateManager()

    preprocessors = []
    for ants in ANNOTATORS:
        if ants:
            anno_names, anno_urls, anno_formatters = zip(
                *[(a['name'], a['url'], a['formatter']) for a in ants])
        else:
            anno_names, anno_urls, anno_formatters = [], [], []
        preprocessors.append(RestCaller(max_workers=MAX_WORKERS, names=anno_names, urls=anno_urls,
                                        formatters=anno_formatters))

    postprocessor = DefaultPostprocessor()
    skill_caller = RestCaller(max_workers=MAX_WORKERS)

    if RESPONSE_SELECTORS:
        rs_names, rs_urls, rs_formatters = zip(
            *[(rs['name'], rs['url'], rs['formatter']) for rs in RESPONSE_SELECTORS])
        response_selector = RestCaller(max_workers=MAX_WORKERS, names=rs_names, urls=rs_urls,
                                       formatters=rs_formatters)
    else:
        response_selector = ConfidenceResponseSelector()

    skill_selector = None
    if SKILL_SELECTORS:
        ss_names, ss_urls, ss_formatters = zip(
            *[(ss['name'], ss['url'], ss['formatter']) for ss in SKILL_SELECTORS])
        skill_selector = RestCaller(max_workers=MAX_WORKERS, names=ss_names, urls=ss_urls,
                                    formatters=ss_formatters)

    skill_manager = SkillManager(skill_selector=skill_selector, response_selector=response_selector,
                                 skill_caller=skill_caller,
                                 profile_handlers=[skill['name'] for skill in SKILLS
                                                   if skill.get('profile_handler')])

    agent = Agent(state_manager, preprocessors, postprocessor, skill_manager)

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

        answers = agent(utterances=utterances, user_telegram_ids=u_tg_ids,
                        user_device_types=u_d_types,
                        date_times=date_times, locations=locations, channel_types=ch_types)
        return answers

    def infer_cmd(messages, dialog_ids):
        utterances: List[Optional[str]] = [message['data'] for message in messages]
        u_ids = [str(message['from_user']['id']) for message in messages]

        date_times = [datetime.utcnow()] * len(messages)
        locations: List[Optional[Location]] = [None] * len(messages)

        answers = agent(utterances=utterances, user_telegram_ids=u_ids,
                        user_device_types=[None] * len(messages),
                        date_times=date_times, locations=locations,
                        channel_types=['cmd_client'] * len(messages))
        return answers

    if CHANNEL == 'telegram':
        return infer_telegram
    else:
        return infer_cmd


async def init_app():
    app = web.Application()
    handle_func = await api_message_processor(run())
    app.router.add_post('/', handle_func)
    app.router.add_get('/dialogs', users_dialogs)
    app.router.add_get('/dialogs/{dialog_id}', dialog)
    return app


async def api_message_processor(message_processor):
    async def api_handle(request):
        result = {}
        if request.method == 'POST':
            if request.headers.get('content-type') != 'application/json':
                raise web.HTTPBadRequest(reason='Content-Type should be application/json')
            data = await request.json()
            user_id = data.get('user_id')
            payload = data.get('payload', '')

            if not user_id:
                raise web.HTTPBadRequest(reason='user_id key is required')

            message = {'data': payload, 'from_user': {'id': user_id}}
            responses = message_processor([message], [1])
            result = {'user_id': user_id, 'response': responses[0]}
        return web.json_response(result)

    return api_handle


async def users_dialogs(request):
    from core.state_schema import Dialog
    exist_dialogs = Dialog.objects()
    result = list()
    for i in exist_dialogs:
        result.append(
            {'id': str(i.id), 'location': i.location, 'channel_type': i.channel_type, 'user': i.user.to_dict()})
    return web.json_response(result)


async def dialog(request):
    from core.state_schema import Dialog
    dialog_id = request.match_info['dialog_id']
    if dialog_id == 'all':
        dialogs = Dialog.objects()
        return web.json_response([i.to_dict() for i in dialogs])
    elif len(dialog_id) == 24 and all(c in hexdigits for c in dialog_id):
        dialog = Dialog.objects(id__exact=dialog_id)
        if not dialog:
            raise web.HTTPNotFound(reason=f'dialog with id {dialog_id} is not exist')
        else:
            return web.json_response(dialog[0].to_dict())
    else:
        raise web.HTTPBadRequest(reason='dialog id should be 24-character hex string')


def main():
    if CHANNEL == 'telegram':
        experimental_bot(run)
    elif CHANNEL == 'cmd_client':
        message_processor = run()
        user_id = input('Provide user id: ')
        user = {'id': user_id}
        while True:
            msg = input(f'You ({user_id}): ').strip()
            if msg:
                message = {'data': msg, 'from_user': user}
                responses = message_processor([message], [1])
                print('Bot: ', responses[0])
    elif CHANNEL == 'http_client':
        app = init_app()
        web.run_app(app, port=args.port)


if __name__ == '__main__':
    main()
