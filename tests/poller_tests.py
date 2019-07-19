import asyncio
import json
import logging
import random
from collections import namedtuple
from dateutil import parser
from multiprocessing import Process

from aiohttp import web

import poller

with open('test_config.json', encoding='utf8') as fin:
    config = json.load(fin)


class PollerTester:
    def __init__(self, tests_keeper):
        self.result = []
        self.messages_to_process = 0
        self.all_messages_processed = asyncio.Event()
        self.all_messages_processed.set()
        self._test_samples = tests_keeper.get_tests()
        self._test_configs = tests_keeper.get_configs()

        # Start poller
        class Crutch:
            def __init__(self):
                Args = namedtuple('Args', ['model_url', 'host', 'port', 'token'])
                self.args = Args(config['model_url'], config['router_bot_host'], f'{config["router_bot_port"]}', config["bot_token"])

            def parse_args(self):
                return self.args

        poller.parser = Crutch()
        log_handler = logging.FileHandler(config['log_file_name'], mode='w')
        log_handler.setFormatter(poller.log_formatter)
        poller.log.addHandler(log_handler)
        poller_process = Process(target=poller.main)
        poller_process.start()

        loop = asyncio.get_event_loop()
        loop.create_task(self._start_tests())
        app = web.Application(loop=loop)
        app.add_routes([web.get('/bot{token}/getUpdates', self._handle_updates),
                        web.post('/bot{token}/sendMessage', self._handle_message)])
        web.run_app(app, port=config["router_bot_port"])

    async def _handle_updates(self, request: web.Request):
        res = self.result
        self.result = []
        if res:
            self.messages_to_process = len(res)
        return web.json_response({'result': res})

    async def _handle_message(self, request: web.Request):
        self.messages_to_process -= 1
        if self.messages_to_process == 0:
            self.all_messages_processed.set()
        return web.Response(status=200)

    async def _start_tests(self):
        for data in self._test_samples:
            await self.all_messages_processed.wait()
            self.all_messages_processed.clear()
            self.result = data
        await self.all_messages_processed.wait()
        await asyncio.sleep(0.2)
        await self._process_log()

    async def _process_log(self):
        tests = {}
        current_test = []
        with open(config['log_file_name'], 'r') as file:
            line = file.readline()
            while line:
                time = parser.parse(line[:23])
                payload = line[29:].strip()
                if 'Payload received' in payload:
                    tests[time] = []
                    current_test = tests[time]
                if 'Sent response to chat' in payload:
                    current_test.append(time)
                line = file.readline()
        for test_n, (test_begin, msgs_sent) in enumerate(tests.items()):
            test_config = self._test_configs[test_n]
            all_test = (msgs_sent[-1] - test_begin).total_seconds()
            msgs_sending = (msgs_sent[-1] - msgs_sent[0]).total_seconds()
            until_first_msg = (msgs_sent[0] - test_begin).total_seconds()
            print(f'Test {test_n}:\n'
                  f'\tPayload:\t\t{test_config["payload"]}\n'
                  f'\tChats:\t\t\t{test_config["num_of_chats"]}\n'
                  f'\tMsgs in chat:\t{test_config["msgs_per_chat"]}\n'
                  f'\tShuffled:\t\t{test_config["shuffle_msgs"]}\n\n'
                  f'Total duration:\t\t{all_test} seconds\n'
                  f'First response in:\t{until_first_msg} seconds\n'
                  f'Responses sent in:\t{msgs_sending} seconds\n')

class TestCasesKeeper:
    def __init__(self, seed: int = 42):
        random.seed(seed)
        self.tests = []
        self.test_configs = []
        for test_case in config['test_cases']:
            test_template = config['test_template'].copy()
            test_template.update(test_case)
            self.test_configs.append(test_template)
            test = []
            for chat_id in range(test_template['num_of_chats']):
                test += [{'message': {'text': test_template['payload'], 'chat': {'id': chat_id}}} for _ in range(test_template['msgs_per_chat'])]
            if test_template['shuffle_msgs']:
                random.shuffle(test)
            self.tests.append(test)

    def get_tests(self):
        return self.tests

    def get_configs(self):
        return self.test_configs


if __name__ == '__main__':
    tk = TestCasesKeeper()
    tester = PollerTester(tk)
