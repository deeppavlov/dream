import asyncio
import random
import time
from collections import namedtuple
from multiprocessing import Process

from aiohttp import web

import poller


class PollerTester:
    def __init__(self, tests: list = None):
        server_port = 7000

        self.result = []
        self.test_start_time = 0
        self.messages_to_process = 0
        self.all_messages_processed = asyncio.Event()
        self.all_messages_processed.set()
        self._test_samples = tests

        # Start poller
        class Crutch:
            def __init__(self):
                Args = namedtuple('Args', ['model_url', 'host', 'port', 'token'])
                self.args = Args('http://0.0.0.0:5000/answer', '0.0.0.0', f'{server_port}', 'some_token')

            def parse_args(self):
                return self.args

        poller.parser = Crutch()
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
            self.test_start_time = time.perf_counter()
        return web.json_response({'result': res})

    async def _handle_message(self, request: web.Request):
        self.messages_to_process -= 1
        if self.messages_to_process == 0:
            test_finish_time = time.perf_counter()
            print(f'took {test_finish_time - self.test_start_time}')
            self.all_messages_processed.set()
        return web.Response(status=200)

    async def _start_tests(self):
        for data in self._test_samples:
            await self.all_messages_processed.wait()
            self.all_messages_processed.clear()
            self.result = data


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
