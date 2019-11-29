import argparse
import asyncio
import logging
import sys
from typing import Dict, List, Union

from aiohttp import web
from aiohttp.web_response import Response

parser = argparse.ArgumentParser()
parser.add_argument('-p', '--port', default=None, type=int)
parser.add_argument('-w', '--watchdog-delay', default=None, type=int)


def ordered(obj):
    if isinstance(obj, dict):
        return sorted((k, ordered(v)) for k, v in obj.items())
    if isinstance(obj, list):
        return [None for x in obj if x is None] + sorted(ordered(x) for x in obj if x is not None)
    else:
        return obj


class Server:
    """Server emulates both router bot and launched as REST api DeepPavlov model.

    Pseudo-DeepPavlov model in "non-convai" and "non-state" mode on each payload returns tuple with upper text and
    unchanged text. In "state" "non-convai" mode model returns tuple with upper text and new state. State must be None
    or List. New state list is obtained by adding request text to the end of the old state list. List with value of
    'first_model_arg' key is returned if old state is None.

    Pseudo-DeepPavlov model in "convai" and "non-state" mode returns tuple with upper text and unchanged text if
    message payload contains text and does not contain command. Model returns tuple with command text if message payload
    contains command. Command text is added to state list in "convai" and "state" mode.

    Non-state non-convai mode example:
        Request payload: {'first_model_arg': ['Text1', 'Text2']}
        Return: [('TEXT1', 'Text1'), ('TEXT2', 'Text2')]

    State non-convai mode example:
        Request payload: {'first_model_arg': ['Text2', 'Text3'], 'second_model_arg': [['Text0', 'Text1'], None]}
        Return: [('TEXT2', ['Text0', 'Text1', 'Text2']), ('TEXT3', ['Text3'])]

    Server endpoints:
        /bot{token}/getUpdates (GET, POST): Returns messages from router bot on GET-request, receives messages from
            router bot on POST-request.
        /bot{token}/sendMessage (POST): Receives messages for router bot.
        /model (POST): Endpoint emulates DeepPavlov REST API endpoint.

    """
    _config: Dict[str, Union[List, Dict, bool]]
    _event: asyncio.Event
    _log: logging.Logger
    _loop: asyncio.events.AbstractEventLoop
    _test_result: Dict[str, bool]
    _watchdog_task: asyncio.Task

    def __init__(self, parsed_args: argparse.Namespace) -> None:
        """Launches aiohttp server.

        Args:
            parsed_args: Arguments from terminal.
        """
        self._config = {
            'convai': False,
            'state': False,
            'poller_input': [],
            'model_input': dict(),
            'expected_output': []
        }
        self._watchdog_delay = parsed_args.watchdog_delay

        log_handler = logging.StreamHandler(sys.stderr)
        self._log = logging.getLogger('server')
        self._log.setLevel(logging.DEBUG)
        self._log.addHandler(log_handler)

        self._loop = asyncio.get_event_loop()
        self._app = web.Application(loop=self._loop)
        self._app.add_routes([web.get('/bot{token}/getUpdates', self._handle_updates),
                              web.post('/bot{token}/getUpdates', self._set_new_test),
                              web.post('/bot{token}/sendMessage', self._handle_message),
                              web.post('/model', self._dp_model)])
        web.run_app(self._app, port=parsed_args.port)

    async def _dp_model(self, request: web.Request) -> Response:
        """Handler for POST-requests to /model endpoint. Simulates DeepPavlov model REST api interface.

        Args:
            request: Request with payload for DeepPavlov model.

        Returns:
            See class docstring.

        """
        data = await request.json()
        self._test_result['model_input_correct'] = (ordered(data) == ordered(self._config['model_input']))
        ret = []
        if self._config['state'] is False:
            for message in data['x']:
                if self._config['convai'] is True:
                    text = message['payload']['text']
                    command = message['payload']['command']
                else:
                    text = message
                    command = None
                resp_list = [text.upper(), text] if command is None else [command]
                ret.append(resp_list)
        else:
            for message, state in zip(data['x'], data['state']):
                if self._config['convai'] is True:
                    text = message['payload']['text']
                    command = message['payload']['command']
                else:
                    text = message
                    command = None
                history = [] if state is None else state
                if command is not None:
                    history.append(command)
                    resp_list = [command, history]
                else:
                    history.append(text)
                    resp_list = [text.upper(), history]
                ret.append(resp_list)
        return web.json_response(ret)

    async def _handle_updates(self, request: web.Request) -> Response:
        """Handler for GET-requests to /bot{token}/getUpdates endpoint."""
        return web.json_response({'result': self._config.pop('poller_input', [])})

    async def _handle_message(self, request: web.Request) -> Response:
        """Handler for POST-requests to /bot{token}/sendMessage endpoint.

        Sets _test_result['poller_output_correct'] True and sets self._event after receiving all correct messages.

        Args:
            request: Request with dictionary to send model response to user. Every correct payload removes item from
                config['expected_output'].

        Returns:
            Response(200)

        """
        data = await request.json()
        try:
            self._config['expected_output'].remove(data)
        except ValueError:
            self._event.set()
        else:
            if not self._config['expected_output']:
                self._watchdog_task.cancel()
                self._test_result['poller_output_correct'] = True
                self._event.set()
        return web.Response(status=200)

    async def _set_new_test(self, request: web.Request) -> Response:
        """Handler for POST-requests to /bot{token}/getUpdates endpoint.

        Method returns response after poller sent all messages to /bot{token}/sendMessage endpoint or after
        self._watchdog_delay s passed (to prevent test from hanging).

        Args:
            request: Request payload must contain dictionary with following keys:
                'convai' (bool): True if dealing with poller in convai mode.
                'state' (bool): True if dealing with poller in state mode
                'poller_input' (List[Dict]): Messages from router bot.
                'model_input' (Dict[str, List]): DeepPavlov model arguments.
                'expected_output' (List[Dict]): Messages that poller sends to /bot{token}/sendMessage endpoint.

        Returns:
            Response contains dictionary with two keys: 'model_input_correct' and 'poller_output_correct'.
            'model_input_correct' value is True if poller send correct payload to DeepPavlov model REST api endpoint
            simulator. 'poller_output_correct' value is True if poller send to router bot's /sendMessage endpoint
            correct messages.
        """
        self._event = asyncio.Event()
        self._test_result = {'model_input_correct': False, 'poller_output_correct': False}
        self._watchdog_task = self._loop.create_task(self._watchdog_timer())
        data = await request.json()
        self._config.update(data)
        await self._event.wait()
        return web.json_response(self._test_result)

    async def _watchdog_timer(self):
        await asyncio.sleep(self._watchdog_delay)
        self._log.info('timer called event.set()')
        self._event.set()


if __name__ == '__main__':
    args = parser.parse_args()
    Server(args)
