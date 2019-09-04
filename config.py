from state_formatters.dp_formatters import *

DB_NAME = 'test'
HOST = '127.0.0.1'
PORT = 27017

MAX_WORKERS = 1

# AGENT_ENV_FILE not used right now, they are redefined in specific docker-compose files (like dev.yml)
AGENT_ENV_FILE = "agent.env"

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
    },
    {
        "name": "transfertransfo",
        "protocol": "http",
        "host": "transfertransfo",
        "port": 8007,
        "endpoint": "transfertransfo",
        "external": True,
        "path": "",
        "formatter": transfertransfo_formatter
    },
    {
        "name": "program_y",
        "protocol": "http",
        "host": "program_y",
        "port": 8008,
        "endpoint": "api/rest/v1.0/ask",
        "external": True,
        "path": "",
        "formatter": program_y_formatter
    },
    {
        "name": "personality_catcher",
        "protocol": "http",
        "host": "personality_catcher",
        "port": 8009,
        "endpoint": "personality_catcher",
        "external": True,
        "path": "",
        "formatter": personality_catcher_formatter
    }
]

ANNOTATORS = [
    {
        "name": "cobot_topics",
        "protocol": "http",
        "host": "cobot_topics",
        "port": 8003,
        "endpoint": "topics",
        "external": True,
        "path": "",
        "formatter": cobot_qa_formatter
    },
    {
        "name": "cobot_sentiment",
        "protocol": "http",
        "host": "cobot_sentiment",
        "port": 8004,
        "endpoint": "sentiment",
        "external": True,
        "path": "",
        "formatter": cobot_qa_formatter
    },
    {
        "name": "cobot_offensiveness",
        "protocol": "http",
        "host": "cobot_offensiveness",
        "port": 8005,
        "endpoint": "offensiveness",
        "external": True,
        "path": "",
        "formatter": cobot_offensiveness_formatter
    },
    {
        "name": "cobot_dialogact",
        "protocol": "http",
        "host": "cobot_dialogact",
        "port": 8006,
        "endpoint": "dialogact",
        "external": True,
        "path": "",
        "formatter": cobot_dialogact_formatter
    }
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
