"""Tests router bot poller correct work with/without state and with/without convai compatibility.

Creates subprocess with router bot and Deeppavlov REST API emulator. Runs router bot poller in another subprocess.

"""

import asyncio
import copy
import json
import time
from string import ascii_lowercase
from subprocess import Popen
from typing import Dict, List, Optional, Tuple

import aiohttp
import pexpect.popen_spawn
from aiohttp import client_exceptions

with open('../config.json', encoding='utf8') as fin:
    poller_config = json.load(fin)
with open('integration_test_config.json', 'r') as conf_file:
    integration_config = json.load(conf_file)
    port = integration_config['emulator_port']
    host = integration_config['emulator_host']

TEST_GRID = []


class Message:
    def __init__(self) -> None:
        self._cmd_template = integration_config['messages']['command']
        self._txt_template = integration_config['messages']['text']
        self._n_letter = 0

    def _get_msg(self, template, chat_id: int) -> Dict:
        msg = copy.deepcopy(template)
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


async def gen_test(convai: bool, state: bool, cmd: List[int], txt: List[int], send_messages: List[Tuple[int, str]],
                   first_batch: Optional[List[str]] = None, state_list: Optional[List] = None) -> None:
    message = Message()
    updates = [message.cmd(chat_id) for chat_id in cmd] + [message.txt(chat_id) for chat_id in txt]
    if convai is True:
        infer = {poller_config["model_args_names"][0]: [t['message'] for t in updates]}
    else:
        infer = {poller_config["model_args_names"][0]: first_batch}
    if state:
        infer[poller_config["model_args_names"][1]] = state_list
    send_msgs = [send_msg(*s) for s in send_messages]
    payload = {'convai': convai, 'state': state, 'updates': updates, 'infer': infer, 'send_messages': send_msgs}
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                await session.post(f'http://{host}:{port}/newTest', json=payload)
                break
            except client_exceptions.ClientConnectionError:
                pass


async def test0():
    await gen_test(convai=False, state=False, cmd=[0], txt=[1, 2], send_messages=[(1, 'A a'), (2, 'B b')], first_batch=['a', 'b'])


async def test1():
    await gen_test(convai=True, state=False, cmd=[0], txt=[1, 2], send_messages=[(0, 'start'), (1, 'A a'), (2, 'B b')])


async def test2():
    await gen_test(convai=False, state=True, cmd=[0], txt=[0], send_messages=[(0, 'A')], first_batch=['a'], state_list=[None])
    await asyncio.sleep(1)

    await gen_test(convai=False, state=True, cmd=[], txt=[0], send_messages=[(0, 'A')], first_batch=['a'], state_list=[['a']])
    await asyncio.sleep(1)

    await gen_test(convai=False, state=True, cmd=[], txt=[0], send_messages=[(0, 'A')], first_batch=['a'], state_list=[['a', 'a']])


async def test3():
    await gen_test(convai=True, state=True, cmd=[0, 1], txt=[], send_messages=[(0, 'start'), (1, 'start')], state_list=[None, None])
    await asyncio.sleep(1)

    await gen_test(convai=True, state=True, cmd=[], txt=[0, 1], send_messages=[(0, 'A'), (1, 'B')], state_list=[['start'], ['start']])
    await asyncio.sleep(1)

    await gen_test(convai=True, state=True, cmd=[], txt=[0, 1], send_messages=[(0, 'A'), (1, 'B')], state_list=[['start', 'a'], ['start', 'b']])

if __name__ == '__main__':
    server = Popen('python router_bot_emulator.py'.split())
    loop = asyncio.get_event_loop()
    for convai, state, foo in zip(['', '--convai', '', '--convai'], ['', '', '--state', '--state'], [test0, test1, test2, test3]):
        poller = pexpect.spawn(' '.join(['python', '../poller.py',
                                         '--port', str(port),
                                         '--host', host,
                                         '--model', f'http://{host}:{port}/answer',
                                         '--token', 'x',
                                         convai,
                                         state]))
        loop.run_until_complete(foo())
        time.sleep(1)
        poller.sendcontrol('c')
        poller.close()

    server.kill()
