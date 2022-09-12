import logging
import os


import sentry_sdk

import common.dialogflow_framework.utils.state as state_utils
import common.utils as common_utils
from common.science import science_topics, SCIENCE_COBOT_TOPICS, SCIENCE_COBOT_DIALOGACTS

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))


logger = logging.getLogger(__name__)


def add_unused_topics(vars, topic):
    shared_memory = state_utils.get_shared_memory(vars)
    unused_topics = shared_memory.get("unused_topics", [])
    state_utils.save_to_shared_memory(vars, unused_topics=list(set(unused_topics + [topic])))


def get_unused_topics(vars):
    shared_memory = state_utils.get_shared_memory(vars)
    unused_topics = shared_memory.get("unused_topics", [])
    return list(set(science_topics.keys()).difference(unused_topics))


def get_supported_cobot_topics(vars):
    topics = common_utils.get_topics(state_utils.get_last_human_utterance(vars), which="all")
    selected_topics = set(topics) & set(SCIENCE_COBOT_TOPICS)
    selected_topics = selected_topics if selected_topics else SCIENCE_COBOT_TOPICS
    return selected_topics


def get_supported_cobot_dialog_topics(vars):
    topics = common_utils.get_topics(state_utils.get_last_human_utterance(vars), which="all")
    selected_topics = set(topics) & set(SCIENCE_COBOT_DIALOGACTS)
    selected_topics = selected_topics if selected_topics else SCIENCE_COBOT_DIALOGACTS
    return selected_topics
