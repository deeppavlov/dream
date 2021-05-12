import re
from common.universal_templates import if_chat_about_particular_topic


GOSSIP_COMPILED_PATTERN = re.compile(
    r"\b(celebrit|actor|actress|writer|author|entrepreneur|sportsperson|musician|gossip)", re.IGNORECASE
)
HAVE_YOU_GOSSIP_TEMPLATE = re.compile(r"(would|have|did|was|had|were|are|do) you .*gossip", re.IGNORECASE)

GOSSIP_SKILL_TRIGGER_PHRASES = [
    "Would you want to hear the latest gossip?",
    "Are you interested in the latest gossip?",
    "Would you be interested in the latest gossip?",
]


def skill_trigger_phrases():
    return GOSSIP_SKILL_TRIGGER_PHRASES


def talk_about_gossip(human_utterance, bot_utterance):
    user_lets_chat_about = if_chat_about_particular_topic(
        human_utterance, bot_utterance, compiled_pattern=GOSSIP_COMPILED_PATTERN
    )
    flag = bool(user_lets_chat_about)
    return flag
