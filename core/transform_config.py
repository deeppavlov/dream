import sys
from os import getenv
from itertools import chain
from copy import deepcopy
from pathlib import Path

import yaml

from core.config import *

# generate component url
for service in chain(ANNOTATORS, SKILL_SELECTORS, SKILLS, RESPONSE_SELECTORS, POSTPROCESSORS):
    host = service['name'] if getenv('DPA_LAUNCHING_ENV') == 'docker' else service['host']
    service['url'] = f"{service['protocol']}://{host}:{service['port']}/{service['endpoint']}"

HOST = 'mongo' if getenv('DPA_LAUNCHING_ENV') == 'docker' else HOST
TELEGRAM_TOKEN = TELEGRAM_TOKEN or getenv('TELEGRAM_TOKEN')
TELEGRAM_PROXY = TELEGRAM_PROXY or getenv('TELEGRAM_PROXY')


def _get_config_path(component_config: dict) -> dict:
    component_config = deepcopy(component_config)
    raw_path = component_config.get('path', None)

    if not raw_path:
        return component_config

    config_path = Path(raw_path)
    if not config_path.is_absolute():
        config_path = Path(__file__).resolve().parents[2] / config_path

    if isinstance(config_path, Path) and config_path.is_file():
        component_config['path'] = config_path
    else:
        raise FileNotFoundError(f'config {raw_path} does not exists')

    return component_config


_run_config_path: Path = Path(__file__).resolve().parent / 'config.yaml'
_component_groups = ['SKILLS', 'ANNOTATORS', 'SKILL_SELECTORS', 'RESPONSE_SELECTORS', 'POSTPROCESSORS']
_module = sys.modules[__name__]

if _run_config_path.is_file():
    with _run_config_path.open('r', encoding='utf-8') as f:
        config: dict = yaml.safe_load(f)

    if config.get('use_config', False) is True:
        config = config.get('agent_config', {})

        MAX_WORKERS = config.get('MAX_WORKERS', MAX_WORKERS)

        DB_NAME = config.get('DB_NAME', DB_NAME)
        HOST = config.get('HOST', HOST)
        PORT = config.get('PORT', PORT)

        for group in _component_groups:
            setattr(_module, group, list(map(_get_config_path, config.get(group, []))))
