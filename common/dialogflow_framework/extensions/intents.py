import logging
import common.dialogflow_framework.utils.state as state_utils
from common.utils import is_yes
from common.dialogflow_framework.extensions.facts_utils import provide_facts_request

logger = logging.getLogger(__name__)


def yes_intent(vars):
    user_uttr = state_utils.get_last_human_utterance(vars)
    flag = is_yes(user_uttr)
    return flag


def always_true(vars):
    return True


def facts(vars):
    return provide_facts_request(vars)
