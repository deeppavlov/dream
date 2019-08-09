"""Tests router bot poller correct work with/without state and with/without convai compatibility.

Creates subprocess with router bot and Deeppavlov REST API emulator. Runs router bot poller in another subprocess.

"""

import json
from multiprocessing import Process
from subprocess import Popen

from poller import Wrapper

with open('../config.json', encoding='utf8') as fin:
    config = json.load(fin)
    config['bot_token'] = 'x'
    config['router_bot_host'] = '0.0.0.0'
    config['router_bot_port'] = '5000'
    for url in ('send_message_url', 'get_updates_url'):
        config[url] = config[f'{url}_template'].format(host=config['router_bot_host'],
                                                       port=config['router_bot_port'],
                                                       token=config['bot_token'])
    config['model_url'] = f"http://{config['router_bot_host']}:{config['router_bot_port']}/answer"

TEST_GRID = []

if __name__ == '__main__':
    server = Popen('python router_bot_emulator.py'.split())
    poller_process = Process(target=Wrapper, args=(config,))
    poller_process.start()
