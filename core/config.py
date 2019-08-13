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
        "path": "skills/text_qa/agent_ru_odqa_retr_noans_rubert_infer.json",
        "env": {
            "CUDA_VISIBLE_DEVICES": ""
        },
        "gpu": False,
        "formatter": odqa_formatter
    },
    {
        "name": "chitchat",
        "protocol": "http",
        "host": "127.0.0.1",
        "port": 2081,
        "endpoint": "chitchat",
        "path": "skills/ranking_chitchat/agent_ranking_chitchat_2staged_tfidf_smn_v4_prep.json",
        "env": {
            "CUDA_VISIBLE_DEVICES": ""
        },
        "profile_handler": True,
        "gpu": False,
        "formatter": chitchat_formatter
    }
]

ANNOTATORS = [
    {
        "name": "ner",
        "protocol": "http",
        "host": "127.0.0.1",
        "port": 2083,
        "endpoint": "ner",
        "path": "annotators/ner/preproc_ner_rus.json",
        "env": {
            "CUDA_VISIBLE_DEVICES": ""
        },
        "gpu": False,
        "formatter": ner_formatter
    },
    {
        "name": "sentiment",
        "protocol": "http",
        "host": "127.0.0.1",
        "port": 2084,
        "endpoint": "intents",
        "path": "annotators/sentiment/preproc_rusentiment.json",
        "env": {
            "CUDA_VISIBLE_DEVICES": ""
        },
        "gpu": False,
        "formatter": sentiment_formatter
    },
    {
        "name": "obscenity",
        "protocol": "http",
        "host": "127.0.0.1",
        "port": 2088,
        "endpoint": "model",
        "path": "annotators/obscenity/obscenity_classifier.json",
        "env": {
            "CUDA_VISIBLE_DEVICES": ""
        },
        "gpu": False,
        "formatter": base_annotator_formatter
    }
]

SKILL_SELECTORS = [
    {
        "name": "chitchat_odqa",
        "protocol": "http",
        "host": "127.0.0.1",
        "port": 2082,
        "endpoint": "intents",
        "path": "skill_selectors/chitchat_odqa_selector/sselector_chitchat_odqa.json",
        "env": {
            "CUDA_VISIBLE_DEVICES": ""
        },
        "gpu": False,
        "formatter": base_annotator_formatter
    }
]
RESPONSE_SELECTORS = []

POSTPROCESSORS = []
