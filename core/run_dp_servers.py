import os
import re
# from multiprocessing import Process
from pathlib import Path
from itertools import islice
from typing import Union, Optional, Dict
from logging import getLogger
import ssl
import argparse

from flasgger import Swagger, swag_from
from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
from deeppavlov.core.commands.infer import build_model
from deeppavlov.core.common.chainer import Chainer

# from core.config import ANNOTATORS, SKILL_SELECTORS, SKILLS, RESPONSE_SELECTORS, POSTPROCESSORS

# from utils.server_utils.server import skill_server
log = getLogger(__name__)
app = Flask(__name__)
Swagger(app)
CORS(app)

pattern = re.compile(r'^https?://(?P<host>.*):(?P<port>\d*)(?P<endpoint>.*)$')

parser = argparse.ArgumentParser()
parser.add_argument('config', type=str)
parser.add_argument('-p', '--port', type=int)
parser.add_argument('-host', '--host', type=str)
parser.add_argument('-ep', '--endpoint', type=str)


def _get_ssl_context(ssl_key, ssl_cert):
    ssh_key_path = Path(ssl_key).resolve()
    if not ssh_key_path.is_file():
        e = FileNotFoundError('Ssh key file not found: please provide correct path in --key param or '
                              'https_key_path param in server configuration file')
        log.error(e)
        raise e

    ssh_cert_path = Path(ssl_cert).resolve()
    if not ssh_cert_path.is_file():
        e = FileNotFoundError('Ssh certificate file not found: please provide correct path in --cert param or '
                              'https_cert_path param in server configuration file')
        log.error(e)
        raise e

    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    ssl_context.load_cert_chain(ssh_cert_path, ssh_key_path)
    return ssl_context


def interact_skill(model: Chainer, batch_size: Optional[int] = None):
    if not request.is_json:
        log.error("request Content-Type header is not application/json")
        return jsonify({
            "error": "request Content-Type header is not application/json"
        }), 400

    data = request.get_json()
    try:
        dialog_states = iter(data['dialogs'])
    except (KeyError, TypeError):
        return jsonify({
            'error': 'illegal payload format'
        }), 500

    responses = []
    while True:
        batch = list(islice(dialog_states, batch_size))
        if not batch:
            break
        try:
            result = model(batch)
        except Exception as e:
            log.error(f'Got an exception when trying to infer the model: {type(e).__name__}: {e}')
            return jsonify({
                'error': f'{type(e).__name__}: {e}'
            }), 500
        if len(model.out_params) == 1:
            result = [result]
        responses += [dict(zip(model.out_params, response)) for response in zip(*result)]

    return jsonify({
        'responses': responses
    }), 200


def skill_server(config: Union[dict, str, Path], https=False, ssl_key=None, ssl_cert=None, *,
                 host: Optional[str] = None, port: Optional[int] = None, endpoint: Optional[str] = None,
                 download: bool = True, batch_size: Optional[int] = None, env: Optional[Dict[str, str]] = None):
    if env:
        os.environ.update(env)
    host = host or '0.0.0.0'
    port = port or 80
    endpoint = f'/{endpoint}' or '/skill'
    if batch_size is not None and batch_size < 1:
        log.warning(f'batch_size of {batch_size} is less than 1 and is interpreted as unlimited')
        batch_size = None

    ssl_context = _get_ssl_context(ssl_key, ssl_cert) if https else None

    model = build_model(config, download=download)

    endpoint_description = {
        'description': 'A skill endpoint',
        'parameters': [
            {
                'name': 'data',
                'in': 'body',
                'required': 'true',
                'example': {
                    'version': '0.9.3',
                    'dialogs': [
                        {
                            'id': '5c65706b0110b377e17eba41',
                            'location': None,
                            'utterances': [
                                {
                                    "id": "5c62f7330110b36bdd1dc5d7",
                                    "text": "Привет!",
                                    "user_id": "5c62f7330110b36bdd1dc5d5",
                                    "annotations": {
                                        "ner": {},
                                        "coref": {},
                                        "sentiment": {},
                                        "obscenity": {}
                                    },
                                    "date": "2019-02-12 16:41:23.142000"
                                },
                                {
                                    "id": "5c62f7330110b36bdd1dc5d8",
                                    "active_skill": "chitchat",
                                    "confidence": 0.85,
                                    "text": "Привет, я бот!",
                                    "user_id": "5c62f7330110b36bdd1dc5d6",
                                    "annotations": {
                                        "ner": {},
                                        "coref": {},
                                        "sentiment": {},
                                        "obscenity": {}
                                    },
                                    "date": "2019-02-12 16:41:23.142000"
                                },
                                {
                                    "id": "5c62f7330110b36bdd1dc5d9",
                                    "text": "Как дела?",
                                    "user_id": "5c62f7330110b36bdd1dc5d5",
                                    "annotations": {
                                        "ner": {},
                                        "coref": {},
                                        "sentiment": {},
                                        "obscenity": {}
                                    },
                                    "date": "2019-02-12 16:41:23.142000"
                                }
                            ],
                            'user': {
                                'id': '5c62f7330110b36bdd1dc5d5',
                                'user_telegram_id': '44d279ea-62ab-4c71-9adb-ed69143c12eb',
                                'user_type': 'human',
                                'device_type': None,
                                'persona': None
                            },
                            'bot': {
                                'id': '5c62f7330110b36bdd1dc5d6',
                                'user_telegram_id': '56f1d5b2-db1a-4128-993d-6cd1bc1b938f',
                                'user_type': 'bot',
                                'device_type': None,
                                'personality': None
                            },
                            'channel_type': 'telegram'
                        }
                    ]
                }
            }
        ],
        'responses': {
            "200": {
                "description": "A skill response",
                'example': {
                    'responses': [{name: 'sample-answer' for name in model.out_params}]
                }
            }
        }
    }

    @app.route('/')
    def index():
        return redirect('/apidocs/')

    @app.route(endpoint, methods=['POST'])
    @swag_from(endpoint_description)
    def answer():
        return interact_skill(model, batch_size)

    app.run(host=host, port=port, threaded=False, ssl_context=ssl_context)


if __name__ == '__main__':
    args = parser.parse_args()
    skill_server(args.config, port=args.port, host=args.host, endpoint=args.endpoint)
