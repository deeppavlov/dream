"""Tests router bot poller work with/without state and with/without convai compatibility.

Creates subprocess with router bot and Deeppavlov REST API emulator. Runs router bot poller in another subprocess.

"""

import asyncio
import copy
import json
from subprocess import Popen
from typing import Dict, List, Optional

import aiohttp
import pexpect.popen_spawn
from aiohttp import client_exceptions


class IntegrationTester:
    def __init__(self, poller_config_path, test_config_path) -> None:
        with open(poller_config_path) as poller_config_file, open(test_config_path) as test_config_file:
            self._config = json.load(test_config_file)
            poller_config = json.load(poller_config_file)
            self.model_args_names = poller_config["model_args_names"]
        self._cmd_template = self._config['messages']['command']
        self._txt_template = self._config['messages']['text']
        self._host = self._config['emulator_host']
        self._port = self._config['emulator_port']

    def _msg(self, chat_id: int, text: Optional[str]) -> Dict:
        template = self._cmd_template if text is None else self._txt_template
        msg = copy.deepcopy(template)
        msg['message']['chat']['id'] = chat_id
        msg['message']['payload']['text'] = text
        return msg

    @staticmethod
    def output_message(chat_id: int, text: str) -> Dict:
        return {'chat_id': chat_id, 'text': f'{{"text": "{text}"}}'}

    async def gen_test(self, test_case: Dict) -> None:
        updates = [self._msg(chat_id, text) for chat_id, text in test_case['poller_input']]
        infer = {arg_name: arg_value for arg_name, arg_value in zip(self.model_args_names, test_case['model_input'])}
        if self._convai is True:
            infer[self.model_args_names[0]] = [t['message'] for t in updates]
        send_msgs = [self.output_message(*s) for s in test_case['expected_output']]
        payload = {'convai': self._convai, 'state': self._state, 'updates': updates, 'infer': infer, 'send_messages': send_msgs}
        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    resp = await session.post(f'http://{self._host}:{self._port}/newTest', json=payload)
                    print(await resp.json())
                    break
                except client_exceptions.ClientConnectionError:
                    pass

    async def test(self, te):
        convai = '--convai' if self._convai else ''
        state = '--state' if self._state else ''
        poller = pexpect.spawn(' '.join(['python', '../poller.py',
                                         '--port', str(self._port),
                                         '--host', self._host,
                                         '--model', f'http://{self._host}:{self._port}/answer',
                                         '--token', 'x',
                                         convai,
                                         state]))
        for test_case in te['test_cases']:
            await self.gen_test(test_case)
        poller.sendcontrol('c')
        poller.close()

    async def run_tests(self):
        for te in self._config['tests']:
            self._convai = te['convai']
            self._state = te['state']
            await self.test(te)


if __name__ == '__main__':
    server = Popen('python router_bot_emulator.py'.split())
    loop = asyncio.get_event_loop()
    tester = IntegrationTester('../config.json', 'integration_test_config.json')
    loop.run_until_complete(tester.run_tests())
    server.kill()
