import argparse
import asyncio
import json
import logging
from logging import config as logging_config

from aiohttp import web

parser = argparse.ArgumentParser()
parser.add_argument('--port', default=5000, type=int)


class Server:
    """Server to emulate router bot.

    Endpoints:
        /bot{token}/getUpdates (get): Returns messages from user.
        /bot{token}/sendMessage (post): Receives payload that passed to Deeppavlov model.
        /answer (post): Enpoint emulates Deeppavlov REST API endpoint.
        /newTest (post): Add messages from user

    """
    def __init__(self, port):
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
        self._log.info('request to model')
        return web.Response(status=200)

    async def _handle_updates(self, request: web.Request):
        self._log.info('request to updates')
        res = self.result
        self.result = []
        if res:
            self.messages_to_process = len(res)
        return web.json_response({'result': res})

    async def _handle_message(self, request: web.Request):
        self._log.info('request to _handle_message')
        return web.Response(status=200)

    async def _set_new_test(self, request: web.Request):
        self._log.info('request to set new test')
        return web.Response(status=200)


if __name__ == '__main__':
    args = parser.parse_args()
    Server(args.port)
