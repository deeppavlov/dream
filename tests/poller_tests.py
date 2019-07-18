import asyncio
import time
from collections import namedtuple
from multiprocessing import Process

from aiohttp import web

import poller


server_port = 7000

class Crutch:
    def __init__(self):
        Args = namedtuple('Args', ['model_url', 'host', 'port', 'token'])
        self.args = Args('http://0.0.0.0:5000/answer', '0.0.0.0', f'{server_port}','some_token')
    def parse_args(self):
        return self.args

loop = asyncio.get_event_loop()
result = []
test_start_time = 0
messages_to_process = 0
all_messages_processed = asyncio.Event()
all_messages_processed.set()

poller.parser = Crutch()
poller_process = Process(target=poller.main)
poller_process.start()

async def handle_updates(request: web.Request):
    global test_start_time, messages_to_process, result, messages_to_process
    test_start_time = time.perf_counter()
    res = result
    if res:
        messages_to_process = len(res)
    result = []
    return web.json_response({'result': res})

async def handle_message(request: web.Request):
    global messages_to_process, test_finish_time, all_messages_processed
    messages_to_process -= 1
    if messages_to_process == 0:
        test_finish_time = time.perf_counter()
        all_messages_processed.set()
    return web.Response(status=200)

async def tests():
    global result, all_messages_processed
    while True:
        await all_messages_processed.wait()
        all_messages_processed.clear()
        result = [{'message':{'text': 'asdf asdf', 'chat': {'id': i}}} for i in range(200)]

if __name__=='__main__':
    loop.create_task(tests())
    app = web.Application(loop=loop)
    app.add_routes([web.get('/bot{token}/getUpdates', handle_updates),
                    web.post('/bot{token}/sendMessage', handle_message)])
    web.run_app(app, port=server_port)