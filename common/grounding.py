import re
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

patterns = ['what are we talking about', 'what it is about',
            'what is it about', 'what we are discussing',
            'what do you mean',
            'i lost common ground']
re_patterns = re.compile('(' + '|'.join(patterns) + ')', re.IGNORECASE)


def what_we_talk_about(utterance):
    if isinstance(utterance, dict):
        utterance = utterance['text']
    return re.search(re_patterns, utterance) is not None

