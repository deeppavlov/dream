"""Tests router bot poller correct work with/without state and with/without convai compatibility.

Creates subprocess with router bot and Deeppavlov REST API emulator. Runs router bot poller in another subprocess.

"""

import asyncio
import copy
import json
import time
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

    def _get_msg(self, template, chat_id: int) -> Dict:
        msg = copy.deepcopy(template)
        msg['message']['date'] = self._date
        self._date += 1.0
        msg['message']['message_id'] = self._message_id
        self._message_id += 1
        msg['message']['chat']['id'] = chat_id
        return msg

    def cmd(self, chat_id: int) -> Dict:
        return self._get_msg(self._cmd_template, chat_id)

    def txt(self, chat_id: int) -> Dict:
        return self._get_msg(self._txt_template, chat_id)


async def start_test(payload: Dict):
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
        'infer': json.dumps({config["model_param_name"]: [t['message']['payload']['text'] for t in updates if t['message']['payload']['text'] is not None]}),
        'send_messages': [json.dumps({'chat_id': chat_id, 'text': json.dumps({'text': "BLAH BLAH BLAH blah blah blah"})}) for chat_id in msg_chat_ids]
    }
    await start_test(payload)


async def test1():
    """convai  = false, state = false"""
    message = Message()
    msg_chat_ids = [1, 2]
    updates = [message.cmd(0)] + [message.txt(i) for i in msg_chat_ids]
    payload = {
        'updates': updates,
        'infer': json.dumps({config["model_param_name"]: [t['message']['payload']['text'] for t in updates if t['message']['payload']['text'] is not None]}),
        'send_messages': [json.dumps({'chat_id': chat_id, 'text': json.dumps({'text': "BLAH BLAH BLAH blah blah blah"})}) for chat_id in msg_chat_ids]
    }
    await start_test(payload)


if __name__ == '__main__':
    server = Popen('python router_bot_emulator.py'.split())
    loop = asyncio.get_event_loop()
    for foo in [test0, test1]:
        poller = pexpect.spawn(
            'python ../poller.py --port 5000 --host 0.0.0.0 --model http://0.0.0.0:5000/answer --token x')
        loop.run_until_complete(foo())
        time.sleep(2)
        poller.sendcontrol('c')
        poller.close()

    server.kill()
