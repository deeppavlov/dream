import asyncio
import json
import random
import re
from collections import namedtuple, defaultdict
from dateutil import parser
from multiprocessing import Process

import numpy as np
from aiohttp import web

from poller import Wrapper, init_log

with open('load_test_config.json', encoding='utf8') as fin:
    config = json.load(fin)
    config["logging"]["handlers"]["log_to_file"]["filename"] = config["log_file_name"]
    config["send_message_url"] = f"http://{config['router_bot_host']}:{config['router_bot_port']}/bot{config['bot_token']}/sendMessage"
    config["get_updates_url"] = f"http://{config['router_bot_host']}:{config['router_bot_port']}/bot{config['bot_token']}/getUpdates"
    init_log(config)


class PollerTester:
    def __init__(self, tests_keeper):
        self.result = []
        self.messages_to_process = 0
        self.all_messages_processed = asyncio.Event()
        self.all_messages_processed.set()
        self._test_samples = tests_keeper.get_tests()
        self._test_configs = tests_keeper.get_configs()

        poller_process = Process(target=Wrapper, args=(config,))
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
        tests = []
        start_pat = re.compile(r'(.*?) INFO Payload received')
        sent_pat = re.compile(r'(.*?) INFO Sent response to chat')
        error_pat = re.compile(r'ERROR Got \d+ code from')
        with open(config['log_file_name'], 'r') as file:
            test_failed = False
            for line in file.readlines():
                for time in start_pat.findall(line):
                    test_failed = False
                    tests.append([parser.parse(time)])
                if error_pat.search(line):
                    test_failed = True
                    tests[-1] = []
                for time in sent_pat.findall(line):
                    if not test_failed:
                        tests[-1].append(parser.parse(time))
        buf = defaultdict(list)
        for test_n, timestamps in enumerate(tests):
            if timestamps:
                test_config = self._test_configs[test_n]
                all_test = (timestamps[-1] - timestamps[0]).total_seconds()
                msgs_sending = (timestamps[-1] - timestamps[1]).total_seconds()
                until_first_msg = (timestamps[1] - timestamps[0]).total_seconds()
                buf[test_config].append((all_test, msgs_sending, until_first_msg))
            else:
                print(f'Test {test_n} failed.\n')
        for test_config, results in buf.items():
            print(f'\tPayload:\t\t{test_config.payload}\n'
                  f'\tChats:\t\t\t{test_config.num_of_chats}\n'
                  f'\tMsgs in chat:\t{test_config.msgs_per_chat}\n'
                  f'\tShuffled:\t\t{test_config.shuffle_msgs}\n\n'
                  f'Total duration:\t\t{np.average([res[0] for res in results]):.3f} seconds, std = {np.std([res[0] for res in results]):.3f}\n'
                  f'First response in:\t{np.average([res[2] for res in results]):.3f} seconds, std = {np.std([res[2] for res in results]):.3f}\n'
                  f'Responses sent in:\t{np.average([res[1] for res in results]):.3f} seconds, std = {np.std([res[1] for res in results]):.3f}\n')

class TestCasesKeeper:
    def __init__(self, seed: int = 42):
        random.seed(seed)
        self.tests = []
        self.test_configs = []
        TestTemplate = namedtuple('TestTemplate', sorted(config['test_template']))
        for test_case in config['test_cases']:
            test_template = config['test_template'].copy()
            test_template.update(test_case)
            test_template = TestTemplate(**test_template)
            for i in range(test_template.repeat_test):
                self.test_configs.append(test_template)
                test = []
                for chat_id in range(test_template.num_of_chats):
                    test += [{'message': {'payload': {'text': test_template.payload}, 'chat': {'id': chat_id}}} for _ in range(test_template.msgs_per_chat)]
                if test_template.shuffle_msgs:
                    random.shuffle(test)
                self.tests.append(test)

    def get_tests(self):
        return self.tests

    def get_configs(self):
        return self.test_configs


if __name__ == '__main__':
    tk = TestCasesKeeper()
    tester = PollerTester(tk)
