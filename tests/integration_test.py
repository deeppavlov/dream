"""Tests router bot poller work with/without state and with/without convai compatibility.

Creates subprocess with router bot and Deeppavlov REST API emulator. Runs router bot poller in another subprocess.

Tests are correct if all values in printed lists is True.

"""

import asyncio
import copy
import json
from subprocess import Popen
from typing import Dict, List, Optional

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
    def __init__(self, tests: List[Dict]) -> None:
        """Initiates IntegrationTester object.

        Args:
            tests: For every test created new poller. Each test contains 3 keys:
                'convai' (bool): True if dealing with poller in convai mode.
                'state' (bool): True if dealing with poller in state mode.
                'test_cases' (List[Dict]): Contains three keys: "poller_input", "expected_output", "model_input".

        'poller_input' (List[List[int, Optional[str]]]): Specifies messages that router bot poller will get from
        /bot{token}/getUpdates endpoint. А message is generated for each element of the 'poller_input' list. First item
        of the element is chat_id (int) of the message. This value is assigned to message['message']['chat']['id'].
        Second item is None or string: command message generated if the item is None and text message generated if
        the item is string. String value is assigned to message['message']['payload']['text'].

        'expected_output' (List[Dict]): Specifies payload that router bot poller will post to /bot{token}/sendMessage
        endpoint. Payload is dict with two items. First key of dictionary is 'chat_id', value is the first element of
        'expected_output' list item. Second key is 'text', value is JSON-serialized dictionary with 'text' key and
        the second element of 'expected_output' list item is value.

        Example:
            'expected_output': [[0, "start"], [1, "A a"]]
            generated list: [{'chat_id': 0, 'text': '{"text": "start"}'}, {'chat_id': 1, 'text': '{"text": "A a"}'}]

        'model_input' (List): Specifies payload that router bot poller will send to DeepPavlov model REST api. Expected
        payload generated accourding this list. In 'non-state' mode 'model_input' list must contain one element to
        specify batch for only first argument of DeepPavlov model. In 'state' mode the list must contain two elements
        to also specify state batch. In 'convai' mode expected payload will be created relying on expected poller input.
        In this case first (in 'non-state' mode also the only) argument must be None. In 'non-convai' mode first
        argument should contain expected batch.

        Example (to simplify, suppose that the first argument of the DeepPavlov model is 'X', second is 'Y'):
            "model_input": [['c'], [['a', 'b']]]
            REST api post payload: {'X': ['c'], 'Y': [['a', 'b']]}

        """
        self._tests = tests

    async def run_tests(self):
        for test in self._tests:
            await self._start_poller(test['convai'], test['state'])

            for test_case in test['test_cases']:
                poller_input = [self._msg(chat_id, text) for chat_id, text in test_case['poller_input']]
                model_input = {arg_name: arg_value for arg_name, arg_value in
                         zip(model_args_names, test_case['model_input'])}
                if test['convai'] is True:
                    model_input[model_args_names[0]] = [t['message'] for t in poller_input]
                expected_output = [self._output_message(*s) for s in test_case['expected_output']]
                payload = {'convai': test['convai'], 'state': test['state'], 'poller_input': poller_input, 'model_input': model_input,
                           'expected_output': expected_output}
                await self._send_updates_to_emulator(payload)

            await self._stop_poller()

    def _msg(self, chat_id: int, text: Optional[str]) -> Dict:
        if text is None:
            template = config['messages']['command']
        else:
            template = config['messages']['text']
        msg = copy.deepcopy(template)
        msg['message']['chat']['id'] = chat_id
        msg['message']['payload']['text'] = text
        return msg

    async def _start_poller(self, convai, state):
        poller_call = ['python ../poller.py', f'--port {port}', f'--host {host}',
                       f'--model http://{host}:{port}/model', f'--token {token}']
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

    @staticmethod
    def _output_message(chat_id: int, text: str) -> Dict:
        return {'chat_id': chat_id, 'text': f'{{"text": "{text}"}}'}


if __name__ == '__main__':
    server = Popen(f'python router_bot_emulator.py -p {port} -w {watchdog_delay}'.split())
    tester = IntegrationTester(config['tests'])
    loop = asyncio.get_event_loop()
    loop.run_until_complete(tester.run_tests())
    server.kill()
