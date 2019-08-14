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
        self._host = self._config['emulator_host']
        self._port = self._config['emulator_port']

    def _msg(self, chat_id: int, text: Optional[str]) -> Dict:
        if text is None:
            template = self._config['messages']['command']
        else:
            template = self._config['messages']['text']
        msg = copy.deepcopy(template)
        msg['message']['chat']['id'] = chat_id
        msg['message']['payload']['text'] = text
        return msg

    @staticmethod
    def output_message(chat_id: int, text: str) -> Dict:
        return {'chat_id': chat_id, 'text': f'{{"text": "{text}"}}'}

    async def _start_poller(self, convai, state):
        poller_call = ['python ../poller.py', f'--port {self._port}', f'--host {self._host}',
                       f'--model http://{self._host}:{self._port}/answer', '--token x']
        if convai is True:
            poller_call.append('--convai')
        if state is True:
            poller_call.append('--state')
        self._poller = pexpect.spawn(' '.join(poller_call))

    async def _stop_poller(self):
        self._poller.sendcontrol('c')
        self._poller.close()

    async def _send_updates_to_emulator(self, payload):
        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    resp = await session.post(f'http://{self._host}:{self._port}/newTest', json=payload)
                    print(await resp.json())
                    break
                except client_exceptions.ClientConnectionError:
                    pass

    async def run_tests(self):
        for test in self._config['tests']:
            await self._start_poller(test['convai'], test['state'])

            for test_case in test['test_cases']:
                poller_input = [self._msg(chat_id, text) for chat_id, text in test_case['poller_input']]
                model_input = {arg_name: arg_value for arg_name, arg_value in
                         zip(self.model_args_names, test_case['model_input'])}
                if test['convai'] is True:
                    model_input[self.model_args_names[0]] = [t['message'] for t in poller_input]
                expected_output = [self.output_message(*s) for s in test_case['expected_output']]
                payload = {'convai': test['convai'], 'state': test['state'], 'poller_input': poller_input, 'model_input': model_input,
                           'expected_output': expected_output}
                await self._send_updates_to_emulator(payload)

            await self._stop_poller()

if __name__ == '__main__':
    server = Popen('python router_bot_emulator.py'.split())
    tester = IntegrationTester('../config.json', 'integration_test_config.json')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(tester.run_tests())
    server.kill()
