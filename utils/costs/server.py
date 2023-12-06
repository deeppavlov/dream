import argparse
import glob
import json
import time
from pathlib import Path
from typing import List

import docker
from docker.models.containers import Container

FILES_LOCATION = Path.home() / 'stats'
FILES_LOCATION.mkdir(parents=True, exist_ok=True)
container_stats_loc = Path('/data/stats')

client = docker.from_env()

pricing = {
    "gpt-4-1106-preview": {
        "input": 0.01,
        "output": 0.03,
    },
    "gpt-4-1106-vision-preview": {
        "input": 0.01,
        "output": 0.03,
    },
    "gpt-4": {
        "input": 0.03,
        "output": 0.06,
    },
    "gpt-4-32k": {
        "input": 0.06,
        "output": 0.12,
    },
    "gpt-35-turbo-1106": {
        "input": 0.001,
        "output": 0.002,
    },
    "gpt-35-turbo-instruct": {
        "input": 0.0015,
        "output": 0.002,
    },
    "gpt-35-turbo": {
        "input": 0.003,
        "output": 0.006,
    },
}


def copy_stats():
    while True:
        openai_containers: List[Container] = [c for c in client.containers.list(all=True, filters={'status': 'running'})
                                              if
                                              'openai' in c.name]
        print(f'got containers {[c.name for c in openai_containers]}')
        for container in openai_containers:
            list_stat = container.exec_run(f'ls {container_stats_loc}')
            container_stats = FILES_LOCATION / container.name
            container_stats.mkdir(parents=True, exist_ok=True)
            if list_stat.exit_code == 0:
                files = [f.decode() for f in list_stat.output.strip().split()]
                print(f'got files {files} in {container.name}')
                for file in files:
                    print(f'writing {container_stats_loc / file} from container to host {container_stats / file}')
                    with open(container_stats / file, 'wb') as fout:
                        fout.write(container.exec_run(f'cat {container_stats_loc / file}').output)
        time.sleep(600)


def get_stats():
    ans = 0
    files = glob.glob(f'{FILES_LOCATION}/**/*.txt', recursive=True)
    for file in files:
        file = Path(file)
        model_name = file.name.split('_')[1]
        with open(file) as fin:
            lines = [json.loads(l) for l in fin.readlines()]
            lines = [l for l in lines if l]
            input_t = sum([l['input_tokens'] for l in lines])
            output_t = sum([l['output_tokens'] for l in lines])
            price = pricing[model_name]
            ans += price['input'] * input_t / 1000 + price['output'] * output_t / 1000
    return ans


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices={'copy', 'count'}, type=str)
    args = parser.parse_args()
    if args.mode == 'copy':
        copy_stats()
    elif args.mode == 'count':
        print(get_stats())
