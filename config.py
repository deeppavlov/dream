from state_formatters.dp_formatters import *

TELEGRAM_TOKEN = ''
TELEGRAM_PROXY = ''

DB_NAME = 'test'
HOST = '127.0.0.1'
PORT = 27017

MAX_WORKERS = 4

SKILLS = [
    {
        "name": "odqa",
        "protocol": "http",
        "host": "127.0.0.1",
        "port": 2080,
        "endpoint": "odqa",
        "path": "odqa/ru_odqa_infer_wiki",
        "env": {
            "CUDA_VISIBLE_DEVICES": ""
        },
        "dockerfile": "dockerfile_skill_cpu",
        "formatter": odqa_formatter
    },
    {
        "name": "chitchat",
        "protocol": "http",
        "host": "127.0.0.1",
        "port": 2081,
        "endpoint": "model",
        "path": "faq/tfidf_autofaq",
        "env": {
            "CUDA_VISIBLE_DEVICES": ""
        },
        "profile_handler": True,
        "dockerfile": "dockerfile_skill_cpu",
        "formatter": odqa_formatter
    }
]

ANNOTATORS = [
    {
        "name": "ner",
        "protocol": "http",
        "host": "127.0.0.1",
        "port": 2083,
        "endpoint": "ner",
        "path": "ner/ner_rus",
        "env": {
            "CUDA_VISIBLE_DEVICES": ""
        },
        "dockerfile": "dockerfile_skill_cpu",
        "formatter": ner_formatter
    },
    {
        "name": "sentiment",
        "protocol": "http",
        "host": "127.0.0.1",
        "port": 2084,
        "endpoint": "intents",
        "path": "classifiers/rusentiment_cnn",
        "env": {
            "CUDA_VISIBLE_DEVICES": ""
        },
        "dockerfile": "dockerfile_skill_cpu",
        "formatter": sentiment_formatter
    }
]

SKILL_SELECTORS = [
    {
        "name": "chitchat_odqa",
        "protocol": "http",
        "host": "127.0.0.1",
        "port": 2082,
        "endpoint": "intents",
        "path": "classifiers/rusentiment_bigru_superconv",
        "env": {
            "CUDA_VISIBLE_DEVICES": ""
        },
        "dockerfile": "dockerfile_skill_cpu",
        "formatter": chitchat_odqa_formatter
    }
]

RESPONSE_SELECTORS = []

POSTPROCESSORS = []
