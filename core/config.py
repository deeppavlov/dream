from state_formatters.dp_formatters import *

TELEGRAM_TOKEN = ''
TELEGRAM_PROXY = ''

DB_NAME = 'test'
HOST = '127.0.0.1'
PORT = 27017

MAX_WORKERS = 1

SKILLS = [
    {
        "name": "alice",
        "protocol": "http",
        "host": "alice",
        "port": 8000,
        "endpoint": "respond",
        "formatter": "alice_formatter",
        "external": True,
        "path": "",
        "formatter": alice_formatter
    }
]

ANNOTATORS = [
]

SKILL_SELECTORS = [
    # {
    #     "name": "chitchat_odqa",
    #     "protocol": "http",
    #     "host": "127.0.0.1",
    #     "port": 2082,
    #     "endpoint": "intents",
    #     "path": "skill_selectors/chitchat_odqa_selector/sselector_chitchat_odqa.json",
    #     "env": {
    #         "CUDA_VISIBLE_DEVICES": ""
    #     },
    #     "gpu": False,
    #     "formatter": base_annotator_formatter
    # }
]
RESPONSE_SELECTORS = []

POSTPROCESSORS = []
