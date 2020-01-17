import argparse
import asyncio
import functools
import json
import logging
from collections import defaultdict, namedtuple
from functools import partial
from itertools import zip_longest
from logging import Logger, config as logging_config
from multiprocessing import Process, Queue
from pathlib import Path
from queue import Empty
from typing import Dict, List, Tuple, Union

import aiohttp
import polling
import requests

log: Logger

parser = argparse.ArgumentParser()
parser.add_argument('--model_url', default=None, help='path to model endpoint', type=str)
parser.add_argument('--host', default=None, help='router bot host', type=str)
parser.add_argument('--port', default=None, help='router bot port', type=str)
parser.add_argument('--token', default=None, help='bot token', type=str)
parser.add_argument('--arg-name', default=None, help='model first argument name', type=str)
parser.add_argument('--state', action='store_true', help='add argument to send state to model')
parser.add_argument('--convai', action='store_true')
parser.add_argument('--agent', action='store_true', help='run poller in dp-agent mode')
parser.add_argument('--empty-text', default="Empty response", help="Empty response text to agent", type=str)


def init_log(conf: Dict) -> None:
    global log
    logging_config.dictConfig(conf["logging"])
    log = logging.root.manager.loggerDict['wrapper_logger']


Message = namedtuple('Message', ['chat_id', 'payload'])


class Wrapper:
    _active_chats: dict
    _backlog: defaultdict

    def __init__(self, config: Dict) -> None:
        self._config = config
        self._in_queue = Queue()
        self._loop = asyncio.get_event_loop()

        self._poller = Poller(config, self._in_queue)
        self._poller.start()
        self._states = {}
        self._active_chats = dict()
        self._backlog = defaultdict(list)
        self._run = True
        log.info('Wrapper initiated')

        try:
            self._loop.run_until_complete(self._poll_msgs())
        except KeyboardInterrupt:
            self._poller.terminate()
            self._poller.join()
            self._run = False
            self._loop.close()

    async def _poll_msgs(self):
        queue_get = partial(self._in_queue.get, timeout=1)
        while self._run:
            try:
                input_q = await self._loop.run_in_executor(None, queue_get)
                self._loop.create_task(self._process_input(input_q))
            except Empty:
                pass

    async def _process_input(self, input_q: Dict) -> None:
        buffer = defaultdict(list)

        for message in input_q['result']:
            chat_id, chat_item = self._process_payload(message['message'])
            if chat_item:
                buffer[chat_id].append(chat_item)
        chats = []
        chat_ids = []

        for chat_id, chat in buffer.items():
            if chat_id in self._active_chats:
                self._backlog[chat_id].extend(chat)
                log.info(f'Message from chat {chat_id} pushed to backlog')
            else:
                chats.append(chat)
                chat_ids.append(chat_id)

        if chats:
            await self._batchify(chats, chat_ids)

    async def _batchify(self, chats: list, chat_ids: list) -> None:
        log.info(f'Processing messages for chats: {chat_ids}')

        for chat_id, chat in zip(chat_ids, chats):
            self._active_chats[chat_id] = len(chat)
        # "slices" of replicas from all conversations, each slice contains replicas from different conversation
        batched_chats = zip_longest(*chats, fillvalue=None)
        for chats_batch in batched_chats:
            await self._process_chats_batch(chats_batch, chat_ids)

    async def _process_chats_batch(self, chats_batch: List[str], chat_ids: List[int]) -> None:
        utts_batch: List[Message] = [Message(chat_id, utt) for chat_id, utt in zip(chat_ids, chats_batch) if utt]
        if self._config['agent_mode'] is True:
            await asyncio.gather(*(self._loop.create_task(self._send_to_agent(msg)) for msg in utts_batch))
        else:
            j = self._config['infer_batch_length']
            chunked_utts_batch = [utts_batch[i * j:(i + 1) * j] for i in range((len(utts_batch) + j - 1) // j)]
            await asyncio.gather(*(self._loop.create_task(self._process_chunk(chunk)) for chunk in chunked_utts_batch))

    async def _send_to_agent(self, msg: Message) -> None:
        chat_id, payload = msg
        data = {'user_id': str(chat_id), 'payload': payload}
        try:
            response = await self._loop.run_in_executor(None, functools.partial(requests.post,
                                                                                self._config['model_url'],
                                                                                json=data,
                                                                                timeout=self._config['request_timeout']))
        except requests.exceptions.ReadTimeout:
            response = requests.Response()
            response.status_code = 503
        if response.status_code == 200:
            resp_text = response.json().get('response')
            resp_text = resp_text or self._config['empty_text']
        else:
            log.error(f'Got {response.status_code} code from {self._config["model_url"]}')
            resp_text = 'Agent error'
        await self._send_results(chat_id, [resp_text])

    async def _process_chunk(self, chunk: List[Message]) -> None:
        ids_batch = [msg.chat_id for msg in chunk]
        utts_batch = [msg.payload for msg in chunk]
        data = {self._config["model_args_names"][0]: utts_batch}
        if self._config['send_state']:
            data[self._config["model_args_names"][1]] = [self._states.get(chat_id) for chat_id in ids_batch]
        try:
            response = await self._loop.run_in_executor(None, functools.partial(requests.post,
                                                                                self._config['model_url'],
                                                                                json=data,
                                                                                timeout=self._config['request_timeout']))
        except requests.exceptions.ReadTimeout:
            response = requests.Response()
            response.status_code = 503

        if response.status_code == 200:
            zip_batch = zip(ids_batch, response.json())
        else:
            log.error(f'Got {response.status_code} code from {self._config["model_url"]}')
            zip_batch = zip_longest(ids_batch, [], fillvalue='Server error')
        tasks = (self._loop.create_task(self._send_results(chat_id, chat_resp)) for (chat_id, chat_resp) in zip_batch)

        await asyncio.gather(*tasks)

    def _process_payload(self, message: Dict) -> Tuple[int, Union[str, dict]]:
        chat_id = message["chat"]["id"]
        if self._config['convai_mode'] is True:
            chat_item = message
        else:
            command = message['payload'].get('command')
            if command is not None:
                log.info(f'Got command "{command}" from chat {chat_id}')
                chat_item = None
            else:
                chat_item = message['payload']['text']
        return chat_id, chat_item

    async def _send_results(self, chat_id: int, response: list) -> None:
        await self._check_backlog(chat_id)
        if self._config['send_state'] is True:
            self._states[chat_id] = response[1]
            resp_text = json.dumps({'text': str(response[0])})
        else:
            buf = {'text': ' '.join(str(element) for element in response)}
            resp_text = json.dumps(buf)

        payload = {
            'chat_id': chat_id,
            'text': resp_text
        }

        async with aiohttp.ClientSession() as session:
            await session.post(self._config['send_message_url'], json=payload)

        log.info(f'Sent response to chat: {str(chat_id)}')

    async def _check_backlog(self, chat_id) -> None:
        self._active_chats[chat_id] -= 1
        if self._active_chats[chat_id] == 0:
            if chat_id in self._backlog:
                chat = self._backlog.pop(chat_id)
                self._loop.create_task(self._batchify([chat], [chat_id]))
            else:
                self._active_chats.pop(chat_id)


class Poller(Process):
    def __init__(self, config: dict, out_queue: Queue):
        super(Poller, self).__init__()
        self.config = config
        self.out_queue = out_queue

    def run(self) -> None:
        while True:
            self._poll()

    def _poll(self) -> None:
        interval = self.config['polling_interval_secs']
        polling_url = self.config['get_updates_url']
        payload = polling.poll(
            lambda: requests.get(polling_url).json(),
            check_success=self._estimate,
            step=interval,
            poll_forever=True,
            ignore_exceptions=(requests.exceptions.ConnectionError, json.decoder.JSONDecodeError, )
        )
        self._process(payload)

    def _estimate(self, payload: dict) -> bool:
        try:
            estimation = True if payload['result'] else False
        except Exception:
            estimation = False
        return estimation

    def _process(self, payload: dict) -> None:
        self.out_queue.put(payload)


def main() -> None:
    args = parser.parse_args()

    model_url = args.model_url
    host = args.host
    port = args.port
    token = args.token
    send_state = args.state
    convai_mode = args.convai
    agent_mode = args.agent
    arg_name = args.arg_name

    root_path = Path(__file__).resolve().parent
    config_path = root_path / 'config.json'
    with open(config_path, encoding='utf8') as fin:
        config = json.load(fin)

    send_message_url: str = config['send_message_url_template']
    get_updates_url: str = config['get_updates_url_template']

    url_params = {
        'host': host or config['router_bot_host'],
        'port': port or config['router_bot_port'],
        'token': token or config['bot_token']
    }

    config['send_message_url'] = send_message_url.format(**url_params)
    config['get_updates_url'] = get_updates_url .format(**url_params)
    config['model_url'] = model_url or config['model_url']
    config['send_state'] = send_state or config['send_state']
    config['convai_mode'] = convai_mode or config['convai_mode']
    config['agent_mode'] = agent_mode or config['agent_mode']
    config['model_args_names'][0] = arg_name or config['model_args_names'][0]
    config['empty_text'] = args.empty_text

    if config['agent_mode'] and (config['convai_mode'] or config['send_state']):
        raise ValueError('one shouldn\'t use --convai or --state arguments with --agent')

    init_log(config)
    Wrapper(config)


if __name__ == '__main__':
    main()
