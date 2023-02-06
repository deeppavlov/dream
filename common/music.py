import re
from common.utils import get_topics, TOPIC_GROUPS

OPINION_REQUESTS_ABOUT_MUSIC = [
    "What kind of music do you like?",
    "What kind of music do you listen to to cheer you up?",
    "What kind of music do you usually listen to?",
    "Who is your favorite singer?",
    "What song do you like to sing?",
    "What is your favorite album?",
    "Who do you think is the best band ever?",
]

MUSIC_COMPILED_PATTERN = re.compile(r"(music|song)", re.IGNORECASE)
ASK_ABOUT_MUSIC = r"(what|which) (music )?(do )?you (like|enjoy)"
MUSIC_REQUEST_RE = r"(alexa[,]? play|alexa[,]? music|play[,]? music|turn music|alexa[,]? song)"

MUSIC_TEMPLATE = (
    r"(\bpop\b|popular music|\brock\b|\brap\b|hip hop|\bpunk\b|heavy metal|jazz|blues|reggae|music|"
    + r"song|progressive trance)"
)
GENRES_TEMPLATE = (
    r"(\bpop\b|popular music|\brock\b|heavy metal|\brap\b|hip hop|\bpunk\b|jazz|blues|reggae|rnb"
    + r"|r\.n\.b\.|are and b\.|r\. and b\.)"
)
VARIOUS_GENRES_TEMPLATE = r"(classic|symphony|contemporary|techno|electro|dubstep|phonk|folk|drill|trance)"


def skill_trigger_phrases():
    return OPINION_REQUESTS_ABOUT_MUSIC


def about_music(annotated_utterance):
    found_topics = get_topics(annotated_utterance, probs=False, which="all")
    if any([music_topic in found_topics for music_topic in TOPIC_GROUPS["music"]]):
        return True
    elif re.findall(MUSIC_COMPILED_PATTERN, annotated_utterance["text"]):
        return True
    else:
        return False
