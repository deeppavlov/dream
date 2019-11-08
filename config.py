from os import getenv

from state_formatters.dp_formatters import *

DB_NAME = getenv('DB_NAME')
DB_HOST = getenv('DB_HOST')
DB_PORT = int(getenv('DB_PORT'))
DB_PATH = getenv('DB_PATH')

MAX_WORKERS = 4

AGENT_ENV_FILE = "agent.env"

SKILLS = [
    # {
    #     "name": "alice",
    #     "protocol": "http",
    #     "host": "alice",
    #     "port": 8000,
    #     "endpoint": "respond",
    #     "external": True,
    #     "path": "",
    #     "formatter": alice_formatter
    # },
    # {
    #     "name": "aiml",
    #     "protocol": "http",
    #     "host": "aiml",
    #     "port": 2080,
    #     "endpoint": "aiml",
    #     "path": "skills/aiml/aiml_skill.json",
    #     "env": {
    #         "CUDA_VISIBLE_DEVICES": ""
    #     },
    #     "gpu": False,
    #     "formatter": aiml_formatter
    # },
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
        "port": 8010,
        "endpoint": "personality_catcher",
        "external": True,
        "path": "",
        "formatter": personality_catcher_formatter
    },
    {
        "name": "retrieval_chitchat",
        "protocol": "http",
        "host": "retrieval_chitchat",
        "port": 8015,
        "endpoint": "retrieval_chitchat",
        "external": True,
        "path": "",
        "formatter": transfertransfo_formatter
    },
    {
        "name": "intent_responder",
        "protocol": "http",
        "host": "intent_responder",
        "port": 8012,
        "endpoint": "respond",
        "external": True,
        "path": "",
        "formatter": intent_responder_formatter
    },
    {
        "name": "dummy_skill",
        "protocol": "http",
        "host": "dummy_skill",
        "port": 8019,
        "endpoint": "respond",
        "external": True,
        "path": "",
        "formatter": dummy_skill_formatter
    },
    {
        "name": "program_y_dangerous",
        "protocol": "http",
        "host": "program_y_dangerous",
        "port": 8022,
        "endpoint": "api/rest/v1.0/ask",
        "external": True,
        "path": "",
        "formatter": program_y_formatter
    },
    {
        "name": "movie_skill",
        "protocol": "http",
        "host": "movie_skill",
        "port": 8023,
        "endpoint": "movie_skill",
        "external": True,
        "path": "",
        "formatter": skill_with_attributes_formatter
    },
]

ANNOTATORS_1 = [
    {
        "name": "sentseg",
        "protocol": "http",
        "host": "sentseg",
        "port": 8011,
        "endpoint": "sentseg",
        "external": True,
        "path": "",
        "formatter": sent_segm_formatter
    },
    {
        "name": "toxic_classification",
        "protocol": "http",
        "host": "toxic_classification",
        "port": 8013,
        "endpoint": "toxicity_annotations",
        "path": "annotators/DeepPavlovToxicClassification/toxic_classification.json",
        "env": {
            "CUDA_VISIBLE_DEVICES": 0
        },
        "gpu": True,
        "formatter": dp_toxic_formatter
    },
    {
        "name": "sentiment_classification",
        "protocol": "http",
        "host": "sentiment_classification",
        "port": 8024,
        "endpoint": "sentiment_annotations",
        "path": "annotators/DeepPavlovSentimentClassification/sentiment_yelp_conv_bert.json",
        "env": {
            "CUDA_VISIBLE_DEVICES": 0
        },
        "gpu": True,
        "formatter": sentiment_formatter
    },
    {
        "name": "blacklisted_words",
        "protocol": "http",
        "host": "blacklisted_words",
        "port": 8018,
        "endpoint": "blacklisted_words",
        "external": True,
        "path": "",
        "formatter": sent_segm_formatter
    }
]

ANNOTATORS_2 = [
    {
        "name": "intent_catcher",
        "protocol": "http",
        "host": "intent_catcher",
        "port": 8014,
        "endpoint": "detect",
        "external": True,
        "path": "",
        "formatter": intent_catcher_formatter
    },
    {
        "name": "ner",
        "protocol": "http",
        "host": "ner",
        "port": 8021,
        "endpoint": "ner",
        "external": True,
        "path": "",
        "formatter": ner_formatter
    },
    {
        "name": "cobot_topics",
        "protocol": "http",
        "host": "cobot_topics",
        "port": 8003,
        "endpoint": "topics",
        "external": True,
        "path": "",
        "formatter": cobot_classifiers_formatter
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
    },
    {
        "name": "cobot_nounphrases",
        "protocol": "http",
        "host": "cobot_nounphrases",
        "port": 8016,
        "endpoint": "nounphrases",
        "external": True,
        "path": "",
        "formatter": punct_dialogs_formatter
    },
    {
        "name": "cobot_offensiveness",
        "protocol": "http",
        "host": "cobot_offensiveness",
        "port": 8005,
        "endpoint": "offensiveness",
        "external": True,
        "path": "",
        "formatter": cobot_classifiers_formatter
    }
]

ANNOTATORS_3 = [
    {
        "name": "sentrewrite",
        "protocol": "http",
        "host": "sentrewrite",
        "port": 8017,
        "endpoint": "sentrewrite",
        "external": True,
        "path": "",
        "formatter": sent_rewrite_formatter
    }
]

SKILL_SELECTORS = [
    {
        "name": "rule_based_selector",
        "protocol": "http",
        "host": "skill_selector",
        "port": 8002,
        "endpoint": "selected_skills",
        "external": True,
        "path": "",
        "formatter": base_skill_selector_formatter
    }
]
RESPONSE_SELECTORS = [
    {
        "name": "convers_evaluation_selector",
        "protocol": "http",
        "host": "repsonse_selector",
        "port": 8009,
        "endpoint": "respond",
        "external": True,
        "path": "",
        "formatter": base_response_selector_formatter
    }
]

POSTPROCESSORS = []

DEBUG = True
