import asyncio
import logging
import random
from collections import namedtuple
from dateutil import parser
from multiprocessing import Process

from aiohttp import web

import poller


class PollerTester:
    def __init__(self, tests: list = None):
        server_port = 7000

        self.result = []
        self.messages_to_process = 0
        self.all_messages_processed = asyncio.Event()
        self.all_messages_processed.set()
        self._test_samples = tests
        self._log_file = 'tests.log'

        # Start poller
        class Crutch:
            def __init__(self):
                Args = namedtuple('Args', ['model_url', 'host', 'port', 'token'])
                self.args = Args('http://0.0.0.0:5000/answer', '0.0.0.0', f'{server_port}', 'some_token')

            def parse_args(self):
                return self.args

        poller.parser = Crutch()
        log_handler = logging.FileHandler(self._log_file, mode='w')
        log_handler.setFormatter(poller.log_formatter)
        poller.log.addHandler(log_handler)
        poller_process = Process(target=poller.main)
        poller_process.start()

        loop = asyncio.get_event_loop()
        loop.create_task(self._start_tests())
        app = web.Application(loop=loop)
        app.add_routes([web.get('/bot{token}/getUpdates', self._handle_updates),
                        web.post('/bot{token}/sendMessage', self._handle_message)])
        web.run_app(app, port=server_port)

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
        await self._process_log()

    async def _process_log(self):
        tests = {}
        current_test = []
        with open(self._log_file, 'r') as file:
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
            all_test = (msgs_sent[-1] - test_begin).total_seconds()
            msgs_sending = (msgs_sent[-1] - msgs_sent[0]).total_seconds()
            until_first_msg = (msgs_sent[0] - test_begin).total_seconds()
            print(f'Test {test_n}:\nTotal duration:\t\t{all_test} seconds:\n'
                  f'First response in:\t{until_first_msg} seconds\n'
                  f'Responses sent in:\t{msgs_sending} seconds\n')

class TestCasesKeeper:
    def __init__(self):
        self.default_msg = 'All work and no play makes Jack a dull boy.'
        self.tests = []

    def add_test(self, chats: list = None, msg: str = None, shuffle: bool = False):
        buf = []
        test = []
        if msg is None:
            msg = self.default_msg
        for chat_id, num_msgs_in_chat in enumerate(chats):
            buf.append([{'message': {'text': msg, 'chat': {'id': chat_id}}} for _ in range(num_msgs_in_chat)])
        for chat in buf:
            test += chat
        if shuffle:
            random.shuffle(test)
        self.tests.append(test)

    def get_tests(self):
        return self.tests


if __name__ == '__main__':
    random.seed(42)
    tk = TestCasesKeeper()
    tk.add_test([200])
    tk.add_test([1 for i in range(200)])
    tester = PollerTester(tk.get_tests())
