import re
import logging

logger = logging.getLogger(__name__)

grounding_patterns = [
    "what do you mean",
    "i lost common ground",
    r"(what|(not|n't) know)(( do| are)( we| you))( talk about| talking about| discuss| discussing)",
    r"(what|(not|n't) know)(( we| you)( do| are))( talk about| talking about| discuss| discussing)",
    r"(what|(not|n't) know)(( it is)|( is it)) about",
    r"^what[\?\.]?$"
]
re_grounding_patterns = re.compile(r"(" + "|".join(grounding_patterns) + r")", re.IGNORECASE)
RE_RECORDING_TEMPLATE = r"(((are|do|can|could|will|would|have|had|whether) " \
                        r"(you|amazon|echo)|conversation( is| (can|could) be)?) " \
                        r"(record|snoop|spy|wiretap|(see(ing)?|watch(ing)?|track(ing)?) " \
                        r"me|listen(ing)? (to )?(me|my)))"
RE_RECORDING_TEMPLATE2 = r"((keep)? (protect) (the)? (information)? (protect|secret))"
re_recording_patterns = re.compile(rf"({RE_RECORDING_TEMPLATE}|{RE_RECORDING_TEMPLATE2})",
                                   re.IGNORECASE)


def are_we_recorded(utterance):
    if isinstance(utterance, dict):
        utterance = utterance["text"]
    return re.search(re_recording_patterns, utterance) is not None


def what_we_talk_about(utterance):
    if isinstance(utterance, dict):
        utterance = utterance["text"]
    return re.search(re_grounding_patterns, utterance) is not None


FAVORITE_INTERRUPT_PATTERN = re.compile(r"my favou?rite[a-z0-9 \-]+is\.?$", re.IGNORECASE)
WHAT_WHO_PATTERN = re.compile(r'(what|who)', re.IGNORECASE)
WHAT_WHO_IS_PATTERN = re.compile(r'(what|who) is[\.\?]?$', re.IGNORECASE)
END_ARTICLE_PATTERN = re.compile(r'( a| an| the| and)[\.\?]?$', re.IGNORECASE)
BUT_PATTERN = re.compile(r" but[\.\?]?$", re.IGNORECASE)
WHEN_PATTERN = re.compile(r" when[\.\?]?$", re.IGNORECASE)
BECAUSE_PATTERN = re.compile(r" because[\.\?]?$", re.IGNORECASE)
BUT_PHRASE = 'But what?'
BECAUSE_PHRASE = 'Because of what?'
WHEN_PHRASE = 'When what?'
REPEAT_PHRASE = "Could you please repeat what you have just said?"


def detect_interrupt(text):
    if re.search(WHAT_WHO_IS_PATTERN, text) or re.search(END_ARTICLE_PATTERN, text):
        return True
    elif not re.search(WHAT_WHO_PATTERN, text) and re.search(FAVORITE_INTERRUPT_PATTERN, text):
        return True
    return False


def detect_end_but(text):
    return re.search(BUT_PATTERN, text)


def detect_end_because(text):
    return re.search(BECAUSE_PATTERN, text)


def detect_end_when(text):
    return re.search(WHEN_PATTERN, text)


MANY_INTERESTING_QUESTIONS = [
    "You have so many interesting questions.",
    "You like to ask interesting questions.",
    "Aren't you the curious one.",
    "You ask a lot of questions, my friend.",
    "You're curious, aren't you?",
    "You so curious. I like it.",
    "I like your curiosity."
]

COMPLIMENT_PROPERTIES = [
    "Considerate",
    "Cooperative",
    "Determined",
    "Enthusiastic",
    "Friendly",
    "Funny",
    "Generous",
    "Helpful",
    "Honest",
    "Insightful",
    "Intelligent",
    "Observant",
    "Organized",
    "Patient",
    "Positive",
    "Proactive",
    "Responsible",
    "Sincere",
    "Wise",
    "Amazing",
    "Awesome",
    "Brilliant",
    "Delightful",
    "Excellent",
    "Fabulous",
    "Fantastic",
    "Gorgeous",
    "Great",
    "Impressive",
    "Lovely",
    "Marvellous",
    "Outstanding",
    "Smashing",
    "Splendid",
    "Wonderful"
]
