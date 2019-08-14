"""Tests router bot poller work with/without state and with/without convai compatibility.

Creates subprocess with router bot and Deeppavlov REST API emulator. Runs router bot poller in another subprocess.

"""

import asyncio
import copy
import json
from subprocess import Popen
from typing import Dict, Optional

import aiohttp
import pexpect.popen_spawn
from aiohttp import client_exceptions

with open('../config.json') as poller_config_file, open('integration_test_config.json') as test_config_file:
    config = json.load(test_config_file)
    poller_config = json.load(poller_config_file)
    model_args_names = poller_config["model_args_names"]
    host = config['emulator_host']
    port = config['emulator_port']
    watchdog_delay = config['watchdog_delay']
    token = 'x'


class IntegrationTester:
    def __init__(self, tests) -> None:
        self._tests = tests

    def _msg(self, chat_id: int, text: Optional[str]) -> Dict:
        if text is None:
            template = config['messages']['command']
        else:
            template = config['messages']['text']
        msg = copy.deepcopy(template)
        msg['message']['chat']['id'] = chat_id
        msg['message']['payload']['text'] = text
        return msg

    @staticmethod
    def output_message(chat_id: int, text: str) -> Dict:
        return {'chat_id': chat_id, 'text': f'{{"text": "{text}"}}'}

    async def _start_poller(self, convai, state):
        poller_call = ['python ../poller.py', f'--port {port}', f'--host {host}',
                       f'--model http://{host}:{port}/answer', f'--token {token}']
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
                    resp = await session.post(f'http://{host}:{port}/bot{token}/getUpdates', json=payload)
                    print(await resp.json())
                    break
                except client_exceptions.ClientConnectionError:
                    pass

    async def run_tests(self):
        for test in self._tests:
            await self._start_poller(test['convai'], test['state'])

            for test_case in test['test_cases']:
                poller_input = [self._msg(chat_id, text) for chat_id, text in test_case['poller_input']]
                model_input = {arg_name: arg_value for arg_name, arg_value in
                         zip(model_args_names, test_case['model_input'])}
                if test['convai'] is True:
                    model_input[model_args_names[0]] = [t['message'] for t in poller_input]
                expected_output = [self.output_message(*s) for s in test_case['expected_output']]
                payload = {'convai': test['convai'], 'state': test['state'], 'poller_input': poller_input, 'model_input': model_input,
                           'expected_output': expected_output}
                await self._send_updates_to_emulator(payload)

            await self._stop_poller()


if __name__ == '__main__':
    server = Popen(f'python router_bot_emulator.py -p {port} -w {watchdog_delay}'.split())
    tester = IntegrationTester(config['tests'])
    loop = asyncio.get_event_loop()
    loop.run_until_complete(tester.run_tests())
    server.kill()
