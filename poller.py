import argparse
import requests
from pathlib import Path
from collections import defaultdict
from multiprocessing import Process, Queue
from itertools import zip_longest

import requests
import polling

from deeppavlov.core.agent.agent import Agent
from deeppavlov.agents.default_agent.default_agent import DefaultAgent
from deeppavlov.skills.default_skill.default_skill import DefaultStatelessSkill
from deeppavlov.core.commands.infer import build_model_from_config
from deeppavlov.core.common.file import read_json
from deeppavlov.deep import find_config

parser = argparse.ArgumentParser()
parser.add_argument("config_path", help="path to a pipeline json config", type=str)


class Wrapper:
    def __init__(self, config: dict, agent: Agent=None):
        self.config = config
        self.agent = agent
        self.in_queue = Queue()

        self.poller = Poller(config, self.in_queue)
        self.poller.start()

        while True:
            input_q = self.in_queue.get()
            self._process_input(input_q)

    def _process_input(self, input_q: dict):
        buffer = defaultdict(list)

        for message in input_q['result']:
            message_text = message['message']['text']
            if self._validate_message(message_text):
                chat_id = message['message']['chat']['id']
                buffer[chat_id].append(message_text)

        chats = []
        chat_ids = []
        for chat_id, chat in buffer.items():
            chats.append(chat)
            chat_ids.append(chat_id)

        batched_chats = zip_longest(*chats, fillvalue=None)
        infer_batches = [list(zip(*[(chat_ids[i], u) for i, u in enumerate(batch) if u])) for batch in batched_chats]

        for infer_batch in infer_batches:
            ids_batch = list(infer_batch[0])
            utterance_batch = list(infer_batch[1])
            response_batch = self.agent(utterance_batch, ids_batch)

            for resp in zip(ids_batch, response_batch):
                self._send_results(*resp)

    def _validate_message(self, message_text: str):
        result = False if message_text[:6] == '/start' or message_text[:4] == '/end' else True
        return result

    def _send_results(self, chat_id, response):
        resp_text = str("{\"text\":\"" + response + "\"}")

        payload = {
            'chat_id': chat_id,
            'text': resp_text
        }

        requests.post(
            url=self.config['send_message_url'],
            json=payload
        )


class Poller(Process):
    def __init__(self, config: dict, out_queue: Queue):
        super(Poller, self).__init__()
        self.config = config
        self.out_queue = out_queue

    def run(self):
        while True:
            self._poll()

    def _poll(self):
        interval = self.config['polling_interval_secs']
        polling_url = self.config['get_updates_url']
        payload = polling.poll(
            lambda: requests.get(polling_url).json(),
            check_success=self._estimate,
            step=interval,
            poll_forever=True,
            ignore_exceptions=(requests.exceptions.ConnectionError,)
        )
        self._process(payload)

    def _estimate(self, payload: dict) -> bool:
        try:
            estimation = True if payload['result'] else False
        except Exception:
            estimation = False
        return estimation

    def _process(self, payload: dict):
        self.out_queue.put(payload)


def main():
    args = parser.parse_args()
    pipeline_config_path = find_config(args.config_path)

    root_path = Path(__file__).resolve().parent
    config_path = root_path / 'config.json'
    config = read_json(config_path)

    send_message_url: str = config['send_message_url_template']
    get_updates_url: str = config['get_updates_url_template']

    url_params = {
        'host': config['router_bot_host'],
        'port': config['router_bot_port'],
        'token': config['bot_token']
    }

    config['send_message_url'] = send_message_url.format(**url_params)
    config['get_updates_url'] = get_updates_url .format(**url_params)

    model = build_model_from_config(pipeline_config_path)
    skill = DefaultStatelessSkill(model)
    agent = DefaultAgent(skills=[skill])
    Wrapper(config, agent)

    while True:
        pass


if __name__ == '__main__':
    main()

