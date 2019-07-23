import aiohttp
import argparse
import asyncio
import functools
import json
import logging
import polling
import requests
import sys
from collections import defaultdict
from itertools import zip_longest
from multiprocessing import Process, Queue
from pathlib import Path
from typing import Optional

logging.disable(logging.DEBUG)
log = logging.getLogger('convai_router_bot_poller')
log.propagate = False
log.setLevel(logging.DEBUG)
log_handler = logging.StreamHandler(sys.stderr)
log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
log_handler.setFormatter(log_formatter)
log.addHandler(log_handler)


parser = argparse.ArgumentParser()
parser.add_argument('model_url', help='path to model endpoint', type=str)
parser.add_argument('--host', default=None, help='router bot host', type=str)
parser.add_argument('--port', default=None, help='router bot port', type=str)
parser.add_argument('--token', default=None, help='bot token', type=str)


class Wrapper:
    def __init__(self, config: dict, model_url=None):
        self.config = config
        self.model_url = model_url
        self.in_queue = Queue()
        self.loop = asyncio.get_event_loop()

        self.poller = Poller(config, self.in_queue)
        self.poller.start()
        self.chat_events = None

        log.info('Wrapper initiated')

        while True:
            input_q = self.in_queue.get()
            log.info('Payload received')
            self.loop.run_until_complete(self._process_input(input_q))

    async def _process_input(self, input_q: dict) -> None:
        buffer = defaultdict(list)

        for message in input_q['result']:
            message_text = self._process_message_text(message['message']['text'])
            if message_text:
                chat_id = message['message']['chat']['id']
                buffer[chat_id].append(message_text)

        chats = []
        chat_ids = []
        log_msg = ''

        for chat_id, chat in buffer.items():
            chats.append(chat)
            chat_ids.append(chat_id)
            log_msg = f'{log_msg}, {str(chat_id)}' if log_msg else f'Processing messages for chats: {str(chat_id)}'

        self.chat_events = {chat_id: [asyncio.Event() for _ in range(len(chat))] for chat_id, chat in buffer.items()}
        for events in self.chat_events.values():
            events[-1].set()

        if log_msg:
            log.info(log_msg)

        # "slices" of replicas from all conversations, each slice contains replicas from different conversation
        batched_chats = zip_longest(*chats, fillvalue=None)

        tasks = (self.loop.create_task(self._process_chats_batch(chats_batch,
                                                                 msg_id,
                                                                 chat_ids)) for msg_id, chats_batch in enumerate(batched_chats))
        await asyncio.gather(*tasks)

    async def _process_chats_batch(self, chats_batch, msg_id, chat_ids):
        utts_batch = [(chat_ids[utt_id], utt) for utt_id, utt in enumerate(chats_batch) if utt]
        j = self.config['infer_batch_length']
        chunked_utts_batch = [utts_batch[i * j:(i + 1) * j] for i in range((len(utts_batch) + j - 1) // j)]
        await asyncio.gather(*(self.loop.create_task(self._process_chunk(chunk, msg_id)) for chunk in chunked_utts_batch))

    async def _process_chunk(self, chunk, msg_id):
        batch = list(zip(*chunk))
        ids_batch = list(batch[0])
        utts_batch = list(batch[1])
        data = {"text1": utts_batch}
        try:
            response = await self.loop.run_in_executor(None, functools.partial(requests.post,
                                                                               self.model_url,
                                                                               json=data,
                                                                               timeout=self.config['request_timeout']))
        except requests.exceptions.ReadTimeout:
            response = requests.Response()
            response.status_code = 503
        if response.status_code == 200:
            tasks = (self.loop.create_task(self._send_results(*resp, msg_id)) for resp in zip(ids_batch, response.json()))
        else:
            log.error(f'Got {response.status_code} code from {self.model_url}')
            tasks = (self.loop.create_task(self._send_results(*resp, msg_id)) for resp in zip_longest(ids_batch, [], fillvalue='Server error'))
        await asyncio.gather(*tasks)

    @staticmethod
    def _process_message_text(message_text: str) -> Optional[str]:
        if message_text[:6] == '/start' or message_text[:4] == '/end':
            processed_message = None
        else:
            processed_message = message_text

        return processed_message

    async def _send_results(self, chat_id, response, msg_id) -> None:
        resp_text = str("{\"text\":\"" + str(response) + "\"}")
        payload = {
            'chat_id': chat_id,
            'text': resp_text
        }
        await self.chat_events[chat_id][msg_id-1].wait()
        async with aiohttp.ClientSession() as session:
            await session.post(self.config['send_message_url'], json=payload)
        self.chat_events[chat_id][msg_id].set()
        # TODO: Refactor logs to log in asynchronous mode
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

    Wrapper(config, model_url)


if __name__ == '__main__':
    main()
