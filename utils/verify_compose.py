"""Making sure that all services from docker-compose.yml are present in dev.yml and proxy.yml"""

import yaml
from pathlib import Path


repo_root = Path(__file__).resolve().parents[1]


def load_yaml(path: Path) -> dict:
    with open(path) as fin:
        return yaml.load(fin, Loader=yaml.FullLoader)


def get_services(compose_file: str) -> set:
    data = load_yaml(repo_root / compose_file)
    return set(data['services'])


def verify_compose():
    compose = get_services('docker-compose.yml')
    compose.remove('agent')
    dev = get_services('dev.yml')
    proxy = get_services('proxy.yml')
    assert not (compose - dev), f'Following services from docker-compose.yml are missing in dev.yml: {compose - dev}'
    assert not (compose - proxy), f'Following services from docker-compose.yml are missing in proxy.yml: ' \
                                  f'{compose - proxy}'
    print('OK')


if __name__ == '__main__':
    verify_compose()
