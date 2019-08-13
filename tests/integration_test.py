"""Tests router bot poller correct work with/without state and with/without convai compatibility.

Creates subprocess with router bot and Deeppavlov REST API emulator. Runs router bot poller in another subprocess.

"""

import asyncio
import copy
import json
import time
from string import ascii_lowercase
from subprocess import Popen
from typing import Dict

import aiohttp
import pexpect.popen_spawn
from aiohttp import client_exceptions

with open('../config.json', encoding='utf8') as fin:
    config = json.load(fin)
    config['bot_token'] = 'x'
    config['router_bot_host'] = '0.0.0.0'
    config['router_bot_port'] = '5000'
    for url in ('send_message_url', 'get_updates_url'):
        config[url] = config[f'{url}_template'].format(host=config['router_bot_host'],
                                                       port=config['router_bot_port'],
                                                       token=config['bot_token'])
    config['model_url'] = f"http://{config['router_bot_host']}:{config['router_bot_port']}/answer"
    config['logging']['loggers']['wrapper_logger']['level'] = 'ERROR'

TEST_GRID = []


class Message:
    def __init__(self) -> None:
        with open('integration_test_config.json', 'r') as conf_file:
            integration_config = json.load(conf_file)
        self._cmd_template = integration_config['messages']['command']
        self._txt_template = integration_config['messages']['text']
        self._message_id = 0
        self._date = self._cmd_template['message']['date']
        self._n_letter = 0

    def _get_msg(self, template, chat_id: int) -> Dict:
        msg = copy.deepcopy(template)
        msg['message']['date'] = self._date
        self._date += 1.0
        msg['message']['message_id'] = self._message_id
        self._message_id += 1
        msg['message']['chat']['id'] = chat_id
        return msg

    def _get_letter(self):
        ret = ascii_lowercase[self._n_letter]
        self._n_letter = (self._n_letter + 1) % len(ascii_lowercase)
        return ret

    def cmd(self, chat_id: int) -> Dict:
        return self._get_msg(self._cmd_template, chat_id)

    def txt(self, chat_id: int) -> Dict:
        msg = self._get_msg(self._txt_template, chat_id)
        msg['message']['payload']['text'] = self._get_letter()
        return msg


def send_msg(chat_id: int, text: str) -> Dict:
    return {'chat_id': chat_id, 'text': f'{{"text": "{text}"}}'}


async def send_test(payload: Dict):
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                await session.post('http://0.0.0.0:5000/newTest', json=payload)
                break
            except client_exceptions.ClientConnectionError:
                pass


async def test0():
    """convai  = false, state = false"""
    message = Message()
    msg_chat_ids = [1, 2]
    updates = [message.cmd(0)] + [message.txt(i) for i in msg_chat_ids]
    payload = {
        'updates': updates,
        'infer': {config["model_args_names"][0]: ['a', 'b']},
        'send_messages': [send_msg(1, "A a"), send_msg(2, "B b")],
        'convai': False,
        'state': False
    }
    await send_test(payload)


async def test1():
    """convai  = true, state = false"""
    message = Message()
    msg_chat_ids = [1, 2]
    updates = [message.cmd(0)] + [message.txt(i) for i in msg_chat_ids]
    payload = {
        'updates': updates,
        'infer': {config["model_args_names"][0]: [t['message'] for t in updates]},
        'send_messages': [send_msg(0, 'start'), send_msg(1, 'A a'), send_msg(2, 'B b')],
        'convai': True,
        'state': False
    }
    await send_test(payload)


async def test2():
    """convai  = false, state = true"""
    message = Message()
    updates = [message.cmd(0), message.txt(0)]
    updates[1]['message']['payload']['text'] = 'first'
    payload = {
        'updates': updates,
        'infer': {config["model_args_names"][0]: ['first'], config['model_args_names'][1]: [None]},
        'send_messages': [send_msg(0, 'FIRST')],
        'convai': False,
        'state': True
    }
    await send_test(payload)
    await asyncio.sleep(3)
    updates = [message.txt(0)]
    updates[0]['message']['payload']['text'] = 'second'
    payload = {
        'updates': updates,
        'infer': {config["model_args_names"][0]: ['second'], config['model_args_names'][1]: [['first']]},
        'send_messages': [send_msg(0, 'SECOND')],
        'convai': False,
        'state': True
    }
    await send_test(payload)
    await asyncio.sleep(3)
    updates = [message.txt(0)]
    updates[0]['message']['payload']['text'] = 'third'
    payload = {
        'updates': updates,
        'infer': {config["model_args_names"][0]: ['third'], config['model_args_names'][1]: [['first', 'second']]},
        'send_messages': [send_msg(0, 'THIRD')],
        'convai': False,
        'state': True
    }
    await send_test(payload)


async def test3():
    """convai  = true, state = true"""
    message = Message()
    updates = [message.cmd(0), message.cmd(1)]
    payload = {
        'updates': updates,
        'infer': {config["model_args_names"][0]: [t['message'] for t in updates], config["model_args_names"][1]: [None, None]},
        'send_messages': [send_msg(0, 'start'), send_msg(1, 'start')],
        'convai': True,
        'state': True
    }
    await send_test(payload)
    await asyncio.sleep(3)
    updates = [message.txt(0), message.txt(1)]
    updates[0]['message']['payload']['text'] = 'first'
    updates[1]['message']['payload']['text'] = 'second'
    payload = {
        'updates': updates,
        'infer': {config["model_args_names"][0]: [t['message'] for t in updates], config["model_args_names"][1]: [['start'], ['start']]},
        'send_messages': [send_msg(0, 'FIRST'), send_msg(1, 'SECOND')],
        'convai': True,
        'state': True
    }
    await send_test(payload)
    await asyncio.sleep(3)
    updates = [message.txt(0), message.txt(1)]
    updates[0]['message']['payload']['text'] = 'third'
    updates[1]['message']['payload']['text'] = 'fourth'
    payload = {
        'updates': updates,
        'infer': {config["model_args_names"][0]: [t['message'] for t in updates], config["model_args_names"][1]: [['start', 'first'], ['start', 'second']]},
        'send_messages': [send_msg(0, 'THIRD'), send_msg(1, 'FOURTH')],
        'convai': True,
        'state': True
    }
    await send_test(payload)

if __name__ == '__main__':
    server = Popen('python router_bot_emulator.py'.split())
    loop = asyncio.get_event_loop()
    for convai, state, foo in zip(['', '--convai', '', '--convai'], ['', '', '--state', '--state'], [test0, test1, test2, test3]):
        poller = pexpect.spawn(
            f'python ../poller.py --port 5000 --host 0.0.0.0 --model http://0.0.0.0:5000/answer --token x {convai} {state}')
        loop.run_until_complete(foo())
        time.sleep(2)
        poller.sendcontrol('c')
        poller.close()

    server.kill()
