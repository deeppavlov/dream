import argparse
import asyncio
import functools
import json
import logging
from collections import defaultdict, namedtuple
from itertools import zip_longest
from logging import Logger, config as logging_config
from multiprocessing import Process, Queue
from pathlib import Path
from typing import Dict, List, Optional

import aiohttp
import requests
import polling

log: Logger

parser = argparse.ArgumentParser()
parser.add_argument('--model_url', default=None, help='path to model endpoint', type=str)
parser.add_argument('--host', default=None, help='router bot host', type=str)
parser.add_argument('--port', default=None, help='router bot port', type=str)
parser.add_argument('--token', default=None, help='bot token', type=str)
parser.add_argument('--state', action='store_true', help='add argument to send state to model')
parser.add_argument('--convai', action='store_true')
parser.add_argument('--agent', action='store_true', help='run poller in dp-agent mode')


def init_log(conf: Dict) -> None:
    global log
    logging_config.dictConfig(conf["logging"])
    log = logging.root.manager.loggerDict['wrapper_logger']


Message = namedtuple('Message', ['chat_id', 'payload'])

class Wrapper:
    _chat_events: Optional[Dict[int, List[asyncio.Event]]]

    def __init__(self, config: Dict) -> None:
        self._config = config
        self._in_queue = Queue()
        self._loop = asyncio.get_event_loop()

        self._poller = Poller(config, self._in_queue)
        self._poller.start()
        self._chat_events = None
        self._states = {}

        log.info('Wrapper initiated')

        while True:
            input_q = self._in_queue.get()
            log.info('Payload received')
            self._loop.run_until_complete(self._process_input(input_q))

    async def _process_input(self, input_q: Dict) -> None:
        buffer = defaultdict(list)

        for message in input_q['result']:
            if self._config['convai_mode'] is True:
                chat_item = message['message']
            else:
                chat_item = self._process_payload(message['message']['payload'])
            if chat_item:
                chat_id = message['message']['chat']['id']
                buffer[chat_id].append(chat_item)

        chats = []
        chat_ids = []
        log_msg = ''

        for chat_id, chat in buffer.items():
            chats.append(chat)
            chat_ids.append(chat_id)
            log_msg = f'{log_msg}, {str(chat_id)}' if log_msg else f'Processing messages for chats: {str(chat_id)}'

        if self._config['send_state'] is False:
            self._chat_events = {chat_id: [asyncio.Event() for _ in range(len(chat))] for chat_id, chat in buffer.items()}
            for events in self._chat_events.values():
                events[-1].set()

        if log_msg:
            log.info(log_msg)

        # "slices" of replicas from all conversations, each slice contains replicas from different conversation
        batched_chats = zip_longest(*chats, fillvalue=None)
        if self._config['send_state'] is True or self._config['agent_mode'] is True:
            for layer_id, chats_batch in enumerate(batched_chats):
                await self._process_chats_batch(chats_batch, layer_id, chat_ids)
        else:
            tasks = (self._loop.create_task(self._process_chats_batch(chats_batch,
                                                                      layer_id,
                                                                      chat_ids)) for layer_id, chats_batch in enumerate(batched_chats))
            await asyncio.gather(*tasks)

    async def _process_chats_batch(self, chats_batch: List[str], layer_id: int, chat_ids: List[int]) -> None:
        utts_batch: List[Message] = [Message(chat_id, utt) for chat_id, utt in zip(chat_ids, chats_batch) if utt]
        if self._config['agent_mode'] is True:
            await asyncio.gather(*(self._loop.create_task(self._send_to_agent(msg, layer_id)) for msg in utts_batch))
        else:
            j = self._config['infer_batch_length']
            chunked_utts_batch = [utts_batch[i * j:(i + 1) * j] for i in range((len(utts_batch) + j - 1) // j)]
            await asyncio.gather(*(self._loop.create_task(self._process_chunk(chunk, layer_id)) for chunk in chunked_utts_batch))

    async def _send_to_agent(self, msg: Message, layer_id: int) -> None:
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
            resp_text = response.json().get('response', 'Empty response')
        else:
            log.error(f'Got {response.status_code} code from {self._config["model_url"]}')
            resp_text = 'Agent error'
        await self._send_results(chat_id, [resp_text], layer_id)

    async def _process_chunk(self, chunk: List[Message], layer_id: int) -> None:
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
        tasks = (self._loop.create_task(self._send_results(chat_id, chat_resp, layer_id)) for (chat_id, chat_resp) in zip_batch)

        await asyncio.gather(*tasks)

    @staticmethod
    def _process_payload(payload: Dict) -> Optional[str]:
        if payload.get('command', None) is not None:
            message = None
        else:
            message = payload['text']
        return message

    async def _send_results(self, chat_id: int, response: list, layer_id: int) -> None:
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

        if self._config['send_state'] is False:
            await self._chat_events[chat_id][layer_id - 1].wait()

        async with aiohttp.ClientSession() as session:
            await session.post(self._config['send_message_url'], json=payload)

        if self._config['send_state'] is False:
            self._chat_events[chat_id][layer_id].set()

        log.info(f'Sent response to chat: {str(chat_id)}')


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

    if config['agent_mode'] and (config['convai_mode'] or config['send_state']):
        raise ValueError('one shouldn\'t use --convai or --state arguments with --agent')

    init_log(config)
    Wrapper(config)


if __name__ == '__main__':
    main()
