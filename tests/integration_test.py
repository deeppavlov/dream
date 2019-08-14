"""Tests router bot poller work with/without state and with/without convai compatibility.

Creates subprocess with router bot and Deeppavlov REST API emulator. Runs router bot poller in another subprocess.

"""

import asyncio
import copy
import json
from string import ascii_lowercase
from subprocess import Popen
from typing import Dict, List, Optional, Tuple

import aiohttp
import pexpect.popen_spawn
from aiohttp import client_exceptions

with open('../config.json', 'r') as config_file, open('integration_test_config.json', 'r') as integration_file:
    poller_config = json.load(config_file)
    integration_config = json.load(integration_file)
    port = integration_config['emulator_port']
    host = integration_config['emulator_host']


class Message:
    def __init__(self, config) -> None:
        self._config = config
        self._convai = config['convai']
        self._state = config['state']
        self._cmd_template = integration_config['messages']['command']
        self._txt_template = integration_config['messages']['text']

    def _msg(self, chat_id: int, text: Optional[str]) -> Dict:
        template = self._cmd_template if text is None else self._txt_template
        msg = copy.deepcopy(template)
        msg['message']['chat']['id'] = chat_id
        msg['message']['payload']['text'] = text
        return msg

    @staticmethod
    def send_msg(chat_id: int, text: str) -> Dict:
        return {'chat_id': chat_id, 'text': f'{{"text": "{text}"}}'}

    async def gen_test(self, test_case: Dict) -> None:
        updates = [self._msg(chat_id, text) for chat_id, text in test_case['poller_input']]
        infer = {arg_name: arg_value for arg_name, arg_value in zip(poller_config["model_args_names"], test_case['model_input'])}
        if self._convai is True:
            infer[poller_config["model_args_names"][0]] = [t['message'] for t in updates]
        send_msgs = [self.send_msg(*s) for s in test_case['expected_output']]
        payload = {'convai': self._convai, 'state': self._state, 'updates': updates, 'infer': infer, 'send_messages': send_msgs}
        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    resp = await session.post(f'http://{host}:{port}/newTest', json=payload)
                    print(await resp.json())
                    break
                except client_exceptions.ClientConnectionError:
                    pass

    async def test(self):
        for test_case in self._config['test_cases']:
            await self.gen_test(test_case)


async def test0():
    message = Message(integration_config['tests'][0])
    await message.test()


async def test1():
    message = Message(integration_config['tests'][1])
    await message.test()


async def test2():
    message = Message(integration_config['tests'][2])
    await message.test()


async def test3():
    message = Message(integration_config['tests'][3])
    await message.test()

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
        poller.sendcontrol('c')
        poller.close()

    server.kill()
