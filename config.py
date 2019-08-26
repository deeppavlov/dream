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
        "external": True,
        "path": "",
        "formatter": alice_formatter
    },
    {
        "name": "aiml",
        "protocol": "http",
        "host": "aiml",
        "port": 2080,
        "endpoint": "aiml",
        "path": "skills/aiml/aiml_skill.json",
        "env": {
            "CUDA_VISIBLE_DEVICES": ""
        },
        "gpu": False,
        "formatter": aiml_formatter
    },
    {
        "name": "cobotqa",
        "protocol": "http",
        "host": "cobotqa",
        "port": 8001,
        "endpoint": "respond",
        "external": True,
        "path": "",
        "formatter": cobot_qa_formatter
    }
]

ANNOTATORS = [
]

SKILL_SELECTORS = [
    {
        "name": "rule_based_selector",
        "protocol": "http",
        "host": "skill_selector",
        "port": 8002,
        "endpoint": "selected_skills",
        "path": "skill_selectors/alexa_skill_selectors/rule_based_selector.json",
        "env": {
            "CUDA_VISIBLE_DEVICES": ""
        },
        "gpu": False,
        "formatter": base_skill_selector_formatter
    }
]
RESPONSE_SELECTORS = []

POSTPROCESSORS = []
