import argparse
import asyncio
import json
import logging
from logging import config as logging_config

from aiohttp import web

parser = argparse.ArgumentParser()
parser.add_argument('--port', default=5000, type=int)


def ordered(obj):
    if isinstance(obj, dict):
        return sorted((k, ordered(v)) for k, v in obj.items())
    if isinstance(obj, list):
        return [None for x in obj if x is None] + sorted(ordered(x) for x in obj if x is not None)
    else:
        return obj


class Server:
    """Server to emulate router bot and DeepPavlov model launched as REST Api.

    DeepPavlov model on each infer returns tuple with upper text and unchanged infer.

    Example:
        'Infer' -> ('INFER', 'Infer')

    Server endpoints:
        /bot{token}/getUpdates (get): Returns messages from user.
        /bot{token}/sendMessage (post): Receives payload that passed to DeepPavlov model.
        /answer (post): Endpoint emulates DeepPavlov REST API endpoint.
        /newTest (post): Add messages from user

    """
    def __init__(self, port):
        self._test_n = 0
        self._updates = []
        self._infer = ''
        self._send_messages = set()
        self._convai = False
        self._state = False
        with open('../config.json', 'r') as config_file:
            config = json.load(config_file)
        logging_config.dictConfig(config['logging'])
        self._log = logging.root.manager.loggerDict['wrapper_logger']
        self._loop = asyncio.get_event_loop()
        self._app = web.Application(loop=self._loop)
        self._app.add_routes([web.get('/bot{token}/getUpdates', self._handle_updates),
                              web.post('/bot{token}/sendMessage', self._handle_message),
                              web.post('/answer', self._dp_model),
                              web.post('/newTest', self._set_new_test)])
        web.run_app(self._app, port=port)

    async def _dp_model(self, request: web.Request):
        data = await request.json()
        self._log.debug(f'Infer is correct: {ordered(data) == ordered(self._infer)}')
        if self._convai is False and self._state is False:
            ret = [(inf.upper(), inf) for inf in data['text1']]
        if self._convai is True and self._state is False:
            ret = []
            for inf in data['text1']:
                text = inf['payload']['text']
                reps_tuple = (text.upper(), text) if text is not None else ['']
                ret.append(reps_tuple)
        if self._convai is False and self._state is True:
            history = [] if data['state'][0] is None else data['state'][0]
            history.append(data['text1'][0])
            ret = [(data['text1'][0].upper(), history)]
        if self._convai is True and self._state is True:
            ret = []
            for tex, stat in zip(data['text1'], data['state']):
                text = tex['payload']['text']
                history = [] if stat is None else stat
                if text is None:
                    text = ""
                    history.append(tex['payload']['command'])
                else:
                    history.append(text)
                ret.append((text.upper(), history))
        return web.json_response(ret)

    async def _handle_updates(self, request: web.Request):
        res = self._updates
        self._updates = []
        return web.json_response({'result': res})

    async def _handle_message(self, request: web.Request):
        data = await request.json()
        self._gen_messages.append(data)
        if ordered(self._send_messages) == ordered(self._gen_messages):
            self._log.debug('All messages received: True')
        return web.Response(status=200)

    async def _set_new_test(self, request: web.Request):
        """Sets test data.

        Request must contain dictionary with following keys:
            'updates' (list): Messages from router bot.
            'infer' (str): Serialized JSON object that router bot poller should send to the DeepPavlov model.
            'send_messages' (List[str]): Each item is serialized JSON object that poller sends to router bot's
                /sendMessage endpoint.

        """
        self._log.debug(f'Test {self._test_n}')
        self._test_n += 1
        data = await request.json()
        self._updates = data['updates']
        self._infer = data['infer']
        self._send_messages = data['send_messages']
        self._convai = data['convai']
        self._state = data['state']
        self._gen_messages = []
        return web.Response(status=200)


if __name__ == '__main__':
    args = parser.parse_args()
    Server(args.port)
