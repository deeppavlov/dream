import logging
import re
from os import getenv
from random import choice

from common.utils import (
    join_words_in_or_pattern,
    join_sentences_in_or_pattern,
    get_topics,
    get_intents,
    get_sentiment,
    is_yes,
    is_no,
    get_entities,
    join_word_beginnings_in_or_pattern,
)
from common.greeting import GREETING_QUESTIONS_TEXTS
import sentry_sdk

logger = logging.getLogger(__name__)

sentry_sdk.init(getenv("SENTRY_DSN"))


GENERATIVE_ROBOT_TEMPLATE = re.compile(
    r"(AI:|Robot:|ROBOT:|Computer:|COMPUTER:|User:|USER:|Speaker:|SPEAKER:|Human:|HUMAN:)\s?"
)
DUMMY_DONTKNOW_RESPONSES = {
    "EN": [
        "What do you want to talk about?",
        "I am a bit confused. What would you like to chat about?",
        "Sorry, probably, I didn't get what you meant. What do you want to talk about?",
        "Sorry, I didn't catch that. What would you like to chat about?",
    ],
    "RU": [
        "О чем ты хочешь поговорить?",
        "Кажется, я немного потерялась. О чем ты хочешь поговорить?",
        "Извини, возможно я не совсем поняла, что ты имеешь в виду. О чем ты хочешь поговорить?",
        "Извини, я не уловила информацию. О чем ты хочешь поболтать?",
    ],
}
# https://www.englishclub.com/vocabulary/fl-asking-for-opinions.htm
UNIVERSAL_OPINION_REQUESTS = [
    "This is interesting, isn't it?",
    "What do you reckon?",
    "What do you think?",
]

NP_OPINION_REQUESTS = [
    "What do you think about NP?",
    "What are your views on NP?",
    "What are your thoughts on NP?",
    "How do you feel about NP?",
    # "I wonder if you like NP.",
    # "Can you tell me do you like NP?",
    # "Do you think you like NP?",
    "I imagine you will have strong opinion on NP.",
    "What reaction do you have to NP?",
    "What's your take on NP?",
    "I'd be very interested to hear your views on NP.",
    "Do you have any particular views on NP?",
    "Any thoughts on NP?",
    "Do you have any thoughts on NP?",
    "What are your first thoughts on NP?",
    # "What is your position on NP?",
    "What would you say if I ask your opinion on NP?",
    "I'd like to hear your opinion on NP.",
]


def opinion_request_question():
    return choice(UNIVERSAL_OPINION_REQUESTS)


FACT_ABOUT_TEMPLATES = [
    "Here's what I've heard.",
    "Hmm.. What do I know? Yes, this.",
    "I recall this.",
    "You know what?",
]


def fact_about_replace():
    return choice(FACT_ABOUT_TEMPLATES)


def nounphrases_questions(nounphrase=None):
    if nounphrase and len(nounphrase) > 0:
        question = choice(NP_OPINION_REQUESTS + UNIVERSAL_OPINION_REQUESTS).replace("NP", nounphrase)
    else:
        question = opinion_request_question()
    return question


ARTICLES = r"\s?(\ba\b|\ban\b|\bthe\b|\bsome\b|\bany\b)?\s?"
ANY_WORDS = r"[a-zA-Zа-яА-ЯйЙёЁ0-9 ]*"
ANY_SENTENCES = r"[A-Za-zа-яА-ЯйЙёЁ0-9-!,\?\.’'\"’ ]*"
END = r"([!,\?\.’'\"’]+.*|$)"
BEGIN_OF_SENT = r"^(.*[!,\?\.’'\"’]+ )?"

ABOUT_LIKE = ["about", "of", "on" + ARTICLES + "topic of"]
QUESTION_LIKE = [
    "let us",
    "let's",
    "lets",
    "let me",
    "do we",
    "do i",
    "do you",
    "can we",
    "can i",
    "can you",
    "could we",
    "could i",
    "could you",
    "will we",
    "will i",
    "will you",
    "would we",
    "would i",
    "would you",
]
START_LIKE = ["start", "begin", "launch", "initiate", "go on", "go ahead", "onset"]
TALK_LIKE = [
    "talk",
    "chat",
    "converse",
    "discuss",
    "speak",
    "tell",
    "say",
    "gossip",
    "commune",
    "chatter",
    "prattle",
    "confab",
    "confabulate",
    "chin",
    "talk smack",
    r"(have|hold|carry on|change|make|take|give me|turn on|"
    r"go into)" + ARTICLES + r"(conversation|talk|chat|discussion|converse|dialog|dialogue|"
    r"speaking|chatter|chitchat|chit chat)",
    f"tell {ANY_WORDS}",
]
WANT_LIKE = [
    "want to",
    "wanna",
    "wish to",
    "need to",
    "desire to",
    r"(would |'d )?(like|love|dream) to",
    "going to",
    "gonna",
    "will",
    "can",
    "could",
    "plan to",
    "in need to",
    "demand",
    "want to",
    "care to",
]
TO_ME_LIKE = [r"to me( now)?", r"with me( now)?", r"me( now)?", "now"]
SOMETHING_LIKE = [
    "anything",
    "something",
    "that",
    "everything",
    "thing",
    "stuff",
    "other things",
    "что-нибудь",
    "что-то",
    "что угодно",
    "всё",
    "что-либо",
    "всякое",
    "другое",
]
NOTHING_LIKE = ["nothing", "none", "neither", "ничего", "нечего", "ни о чем", "не о чем", r"ни то,? ни то"]
DONOTKNOW_LIKE = [
    r"(i )?(do not|don't) know",
    "you (choose|decide|pick up)",
    "hard (to say|one)",
    "none",
    r"(я )?(не знаю|без понятия)",
    "(ты|сам) (выбери|выбирай|реши|решай)",
    "сложно (сказать|выбрать)",
]
KNOW_LIKE = ["know", "learn", "find out"]
LIKE_TEMPLATE = ["like", "love", "prefer"]
ASK_TEMPLATE = ["ask", "request"]

# talk to me, talk with me, talk, talk with me now, talk now.
TALK_TO_ME = join_words_in_or_pattern(TALK_LIKE) + r"(\s" + join_words_in_or_pattern(TO_ME_LIKE) + r")?"
ABOUT_SOMETHING = join_words_in_or_pattern(ABOUT_LIKE) + r"?\s" + join_words_in_or_pattern(SOMETHING_LIKE)
SOMETHING_WITH_SPACES = r"\s?" + join_words_in_or_pattern(SOMETHING_LIKE) + r"?\s?"
ABOUT_TOPIC = join_words_in_or_pattern(ABOUT_LIKE) + r"\s" + ANY_WORDS
KNOW = join_words_in_or_pattern(KNOW_LIKE)
SOMETHING_ELSE = re.compile(
    r"((something|anything|everything|что-нибудь|что-то|что угодно|что-либо) (else|other|другом|другое))", re.IGNORECASE
)

# --------------- Let's talk. / Can we talk? / Talk to me. ------------
COMPILE_LETS_TALK = re.compile(
    join_sentences_in_or_pattern(
        [
            TALK_TO_ME + END,
            join_words_in_or_pattern(QUESTION_LIKE) + r"\s?" + TALK_TO_ME + END,
            join_words_in_or_pattern(WANT_LIKE) + r"\s?" + TALK_TO_ME + END,
            join_words_in_or_pattern(START_LIKE) + r"\s?" + TALK_TO_ME + END,
        ]
    ),
    re.IGNORECASE,
)

# --------------- I don't want to talk. / I don't want to talk about that. ------------
COMPILE_NOT_WANT_TO_TALK_ABOUT_IT = re.compile(
    join_sentences_in_or_pattern(
        [
            r"(not|n't|\bno\b) " + join_words_in_or_pattern(WANT_LIKE) + r"\s?" + join_words_in_or_pattern(TALK_LIKE),
            r"(not|n't|\bno\b) " + join_words_in_or_pattern(TALK_LIKE),
            r"(not|n't|\bno\b) " + join_words_in_or_pattern(LIKE_TEMPLATE),
            r"(not|n't|\bno\b) " + join_words_in_or_pattern(ASK_TEMPLATE),
        ]
    ),
    re.IGNORECASE,
)

# ----- Let's talk about something. / Can we talk about something? / Talk to me about something. ----
COMPILE_LETS_TALK_ABOUT_SOMETHING = re.compile(
    join_sentences_in_or_pattern(
        [
            TALK_TO_ME + r"\s?" + ABOUT_SOMETHING + END,
            join_words_in_or_pattern(QUESTION_LIKE) + r"\s?" + TALK_TO_ME + r"\s?" + ABOUT_SOMETHING + END,
            join_words_in_or_pattern(WANT_LIKE) + r"\s?" + TALK_TO_ME + r"\s?" + ABOUT_SOMETHING + END,
            join_words_in_or_pattern(START_LIKE) + r"\s?" + TALK_TO_ME + r"\s?" + ABOUT_SOMETHING + END,
            r"\bi\s" + join_words_in_or_pattern(WANT_LIKE) + r"\s?" + KNOW + r"\s?" + ABOUT_SOMETHING + END,
            r"why (do not|don't) (we|us|me|you|to) " + TALK_TO_ME + r"\s?" + ABOUT_SOMETHING + END,
        ]
    ),
    re.IGNORECASE,
)

# ----- Let's talk about something ELSE. / Can we talk about something ELSE? / Talk to me about something ELSE. ----
# ----- .. switch the topic. / .. next topic. / .. switch topic. / Next. ----
COMPILE_SWITCH_TOPIC = re.compile(
    join_sentences_in_or_pattern(
        [
            BEGIN_OF_SENT + TALK_TO_ME + r"\s?" + ABOUT_SOMETHING + " else" + END,
            join_words_in_or_pattern(QUESTION_LIKE) + r"\s?" + TALK_TO_ME + r"\s?" + ABOUT_SOMETHING + " else" + END,
            join_words_in_or_pattern(WANT_LIKE) + r"\s?" + TALK_TO_ME + r"\s?" + ABOUT_SOMETHING + " else" + END,
            join_words_in_or_pattern(START_LIKE) + r"\s?" + TALK_TO_ME + r"\s?" + ABOUT_SOMETHING + " else" + END,
            r"(switch|change|next)" + ARTICLES + "topic" + END,
            r"^next" + END,
            r"\bi\s" + join_words_in_or_pattern(WANT_LIKE) + r"\s?" + KNOW + r"\s" + ABOUT_SOMETHING + " else" + END,
        ]
    ),
    re.IGNORECASE,
)

# ----- Let's talk about TOPIC. / Can we talk about TOPIC? / Talk to me about TOPIC. ----
COMPILE_LETS_TALK_ABOUT_TOPIC = re.compile(
    join_sentences_in_or_pattern(
        [
            TALK_TO_ME + SOMETHING_WITH_SPACES + ABOUT_TOPIC + END,
            join_words_in_or_pattern(QUESTION_LIKE) + r"\s?" + TALK_TO_ME + SOMETHING_WITH_SPACES + ABOUT_TOPIC + END,
            join_words_in_or_pattern(WANT_LIKE) + r"\s?" + TALK_TO_ME + SOMETHING_WITH_SPACES + ABOUT_TOPIC + END,
            join_words_in_or_pattern(START_LIKE) + r"\s?" + TALK_TO_ME + SOMETHING_WITH_SPACES + ABOUT_TOPIC + END,
            BEGIN_OF_SENT + "discuss" + r"\s" + ANY_WORDS + END,
            join_words_in_or_pattern(QUESTION_LIKE) + r"\s?" + "discuss" + r"\s" + ANY_WORDS + END,
            join_words_in_or_pattern(WANT_LIKE) + r"\s?" + "discuss" + r"\s" + ANY_WORDS + END,
            join_words_in_or_pattern(START_LIKE) + r"\s?" + "discuss" + r"\s" + ANY_WORDS + END,
            r"\bi\s" + join_words_in_or_pattern(WANT_LIKE) + r"\s?" + KNOW + SOMETHING_WITH_SPACES + ABOUT_TOPIC + END,
            r"why (do not|don't) (we|us|me|you|to) " + TALK_TO_ME + r"\s?" + ABOUT_TOPIC + END,
            r"why (do not|don't) (we|us|me|you|to) " + "discuss" + r"\s" + ANY_WORDS + END,
        ]
    ),
    re.IGNORECASE,
)

WHAT_TO_TALK_ABOUT = (
    r"what (do|can|could|will|would|are) (you|we|i) "
    + join_words_in_or_pattern(WANT_LIKE)
    + r"\s"
    + join_words_in_or_pattern(TALK_LIKE)
    + r"\s"
    + join_words_in_or_pattern(ABOUT_LIKE)
    + END
)
PICK_UP_THE_TOPIC = r"(pick up|choose|select|give)( me)?" + ARTICLES + r"topic" + END
ASK_ME_SOMETHING = r"(ask|tell|say)( me)?" + join_words_in_or_pattern(SOMETHING_LIKE) + END
WHATS_ON_YOUR_MIND = r"what('s| is) on your mind"

# ----- What do you want to talk about? / Pick up the topic. / Ask me something. ----
COMPILE_WHAT_TO_TALK_ABOUT = re.compile(
    join_sentences_in_or_pattern([WHAT_TO_TALK_ABOUT, PICK_UP_THE_TOPIC, ASK_ME_SOMETHING, WHATS_ON_YOUR_MIND]),
    re.IGNORECASE,
)

# ----- Something. / Anything. / Nothing. ----
COMPILE_SOMETHING = re.compile(
    join_sentences_in_or_pattern(
        [
            join_words_in_or_pattern(SOMETHING_LIKE),
            join_words_in_or_pattern(NOTHING_LIKE),
            join_words_in_or_pattern(DONOTKNOW_LIKE),
        ]
    )
    + END,
    re.IGNORECASE,
)

LIKE_WORDS = r"\b(prefer|adore|enjoy|love|like|stand|into\b|fond of|passionate of|crazy|appreciate|interested|fan\b)"
LIKE_PATTERN = re.compile(LIKE_WORDS, re.IGNORECASE)

NOT_LIKE_PATTERN = re.compile(
    rf"(hate|loathe|((not|n't) |dis|un)({LIKE_WORDS}|for (me|you)\b)|[a-z ]+\bfan\b)", re.IGNORECASE
)

STOP_PATTERN = re.compile(r"(stop|shut|something else|change|don't want)", re.IGNORECASE)
CONTINUE_PATTERN = re.compile(r"(continue|more|go ahead)", re.IGNORECASE)


def if_lets_chat(uttr):
    uttr_ = uttr.lower()
    if re.search(COMPILE_LETS_TALK, uttr_):
        return True
    else:
        return False


def if_lets_chat_about_topic(uttr):
    uttr_ = uttr.lower()
    # True if `let's talk about particular-topic`
    if not re.search(COMPILE_NOT_WANT_TO_TALK_ABOUT_IT, uttr_):
        if re.search(COMPILE_LETS_TALK_ABOUT_SOMETHING, uttr_):
            return False
        elif re.search(COMPILE_SWITCH_TOPIC, uttr_):
            return False
        elif re.search(COMPILE_LETS_TALK_ABOUT_TOPIC, uttr_):
            return True
        else:
            return False
    else:
        return False


def if_switch_topic(uttr):
    uttr_ = uttr.lower()
    if re.search(COMPILE_SWITCH_TOPIC, uttr_):
        return True
    else:
        return False


def book_movie_music_found(annotated_uttr):
    topics = set(get_topics(annotated_uttr, which="all"))
    target_topics = {
        "Entertainment_Books",
        "Books&Literature",
        "Movies_TV",
        "Entertainment_Movies",
        "Music",
        "Entertainment_Music",
    }
    target_topic_met = len(target_topics & topics) > 0
    return target_topic_met


def is_switch_topic(annotated_uttr):
    topic_switch_detected = False  # "Topic_SwitchIntent" in get_intents(annotated_uttr, which="all")

    if topic_switch_detected or if_switch_topic(annotated_uttr["text"].lower()):
        return True
    else:
        return False


def if_choose_topic(annotated_uttr, prev_annotated_uttr=None):
    """Dialog context implies that the next utterances can pick up a topic:
    - annotated_uttr asks to switch topic
    - annotated_uttr asks "what do you want to talk about?"
    - annotated_uttr asks "let's talk about something (else)"
    - prev_annotated_uttr asks "what do you want to talk about?", and annotated_uttr says something/anything.
    """
    prev_annotated_uttr = {} if prev_annotated_uttr is None else prev_annotated_uttr
    uttr_ = annotated_uttr.get("text", "").lower()
    prev_uttr_ = prev_annotated_uttr.get("text", "--").lower()
    chat_about_intent = "lets_chat_about" in get_intents(annotated_uttr, probs=False, which="intent_catcher")
    user_asks_what_to_talk_about = re.search(COMPILE_WHAT_TO_TALK_ABOUT, uttr_)
    # user ask to "talk about something"
    smth1 = re.search(COMPILE_LETS_TALK_ABOUT_SOMETHING, uttr_) or (
        chat_about_intent and re.search(COMPILE_SOMETHING, uttr_)
    )
    # bot asks "what user wants to talk about", and user answers "something"
    prev_chat_about_intent = "lets_chat_about" in get_intents(prev_annotated_uttr, probs=False, which="intent_catcher")
    prev_uttr_asks_what_topic = prev_chat_about_intent or re.search(COMPILE_WHAT_TO_TALK_ABOUT, prev_uttr_)
    smth2 = prev_uttr_asks_what_topic and re.search(COMPILE_SOMETHING, uttr_)

    switch_topic = is_switch_topic(annotated_uttr)
    if switch_topic or user_asks_what_to_talk_about or (smth1 or smth2):
        return True
    return False


def if_not_want_to_chat_about_particular_topic(annotated_uttr, prev_annotated_uttr={}):
    uttr_ = annotated_uttr.get("text", "")
    if re.search(COMPILE_NOT_WANT_TO_TALK_ABOUT_IT, uttr_):
        return True

    # prev uttr is what do you want to talk about?
    prev_chat_about_intent = "lets_chat_about" in get_intents(prev_annotated_uttr, probs=False, which="intent_catcher")
    prev_what_to_chat_about = prev_chat_about_intent or if_utterance_requests_topic(prev_annotated_uttr)
    if prev_what_to_chat_about and is_no(annotated_uttr):
        # previously offered to chat about topic, user declines
        return True
    elif prev_what_to_chat_about and is_switch_topic(annotated_uttr):
        # previously offered to chat about topic, user asks to switch topic
        return True
    elif prev_what_to_chat_about and SOMETHING_ELSE.search(uttr_):
        # previously offered to chat about topic, user asks to something else
        return True

    # current uttr is lets talk about something else / other than
    chat_about_intent = "lets_chat_about" in get_intents(annotated_uttr, probs=False, which="intent_catcher")
    chat_about = chat_about_intent or if_lets_chat_about_topic(uttr_)
    if chat_about and SOMETHING_ELSE.search(uttr_):
        return True
    return False


ANY_TOPIC_AMONG_OFFERED = re.compile(
    r"(\bany\b|\ball\b|\beither\b|\bboth\b|don't know|not know" r"|you (choose|pick up|tell me|want|wish|like)\.?$)"
)


def if_utterance_requests_topic(annotated_uttr):
    uttr_text_lower = annotated_uttr.get("text", "").lower()
    prev_was_greeting = any([greeting_question in uttr_text_lower for greeting_question in GREETING_QUESTIONS_TEXTS])

    prev_what_to_talk_about_regexp = re.search(COMPILE_WHAT_TO_TALK_ABOUT, uttr_text_lower)
    if prev_was_greeting or prev_what_to_talk_about_regexp:
        return True
    return False


def if_chat_about_particular_topic(annotated_uttr, prev_annotated_uttr=None, key_words=None, compiled_pattern=r""):
    """Dialog context implies that the last utterances chooses particular conversational topic:
    - annotated_uttr asks "let's talk about PARTICULAR-TOPIC"
    - prev_annotated_uttr asks "what do you want to talk about?", and annotated_uttr says PARTICULAR-TOPIC.
    - prev_annotated_uttr asks "what are your interests?", and annotated_uttr says PARTICULAR-TOPIC.
    """
    prev_annotated_uttr = {} if prev_annotated_uttr is None else prev_annotated_uttr
    key_words = [] if key_words is None else key_words
    uttr_ = annotated_uttr.get("text", "").lower()
    prev_uttr_ = prev_annotated_uttr.get("text", "").lower()

    # current uttr is lets talk about blabla
    chat_about_intent = "lets_chat_about" in get_intents(annotated_uttr, probs=False, which="intent_catcher")
    chat_about = chat_about_intent or if_lets_chat_about_topic(uttr_)

    # prev uttr is what do you want to talk about?
    prev_chat_about_intent = "lets_chat_about" in get_intents(prev_annotated_uttr, probs=False, which="intent_catcher")
    prev_what_to_chat_about = prev_chat_about_intent or if_utterance_requests_topic(prev_annotated_uttr)

    not_want = if_not_want_to_chat_about_particular_topic(annotated_uttr, prev_annotated_uttr)
    if not_want:
        return False
    elif prev_what_to_chat_about or chat_about:
        if key_words:
            trigger_pattern = re.compile(
                rf"{join_word_beginnings_in_or_pattern(key_words)}[a-zA-Z0-9,\-\' ]+\?", re.IGNORECASE
            )
            offered_this_topic = trigger_pattern.search(prev_uttr_)
            user_agrees_or_any = ANY_TOPIC_AMONG_OFFERED.search(uttr_) or is_yes(annotated_uttr)
            if any([word in uttr_ for word in key_words]) or (offered_this_topic and user_agrees_or_any):
                return True
            else:
                return False
        elif compiled_pattern:
            if isinstance(compiled_pattern, str):
                offered_this_topic = re.search(rf"{compiled_pattern}[a-zA-Z0-9,\-\' ]+\?", prev_uttr_, re.IGNORECASE)
            else:
                offered_this_topic = re.search(
                    rf"{compiled_pattern.pattern}[a-zA-Z0-9,\-\' ]+\?", prev_uttr_, re.IGNORECASE
                )
            user_agrees_or_any = ANY_TOPIC_AMONG_OFFERED.search(uttr_) or is_yes(annotated_uttr)
            if re.search(compiled_pattern, uttr_) or (offered_this_topic and user_agrees_or_any):
                return True
            else:
                return False
        else:
            return True
    return False


def is_negative(annotated_uttr):
    sentiment = get_sentiment(annotated_uttr, probs=False)[0]
    return sentiment in ["negative", "very_negative"]


def is_positive(annotated_uttr):
    sentiment = get_sentiment(annotated_uttr, probs=False)[0]
    return sentiment in ["positive", "very_positive"]


def is_neutral(annotated_uttr):
    sentiment = get_sentiment(annotated_uttr, probs=False)[0]
    return sentiment in ["neutral"]


more_details_pattern = re.compile(r"(\bmore\b|detail)", re.IGNORECASE)


def tell_me_more(annotated_uttr):
    intents = get_intents(annotated_uttr, which="intent_catcher", probs=False)
    cond1 = "tell_me_more" in intents
    cond2 = re.search(more_details_pattern, annotated_uttr["text"])
    return cond1 or cond2


QUESTION_BEGINNINGS = [
    r"what'?s?",
    "when",
    "where",
    "which",
    r"who'?s?",
    "whom",
    "whose",
    r"how'?s?",
    "why",
    "whether",
    "do (i|we|you|they)",
    "does (it|he|she)",
    "have (i|we|you|they)",
    "has (it|he|she)",
    "can (i|it|we|you|they)",
    "could (i|it|we|you|they)",
    "shall (i|we|you|they)",
    "should (i|it|we|you|they)",
    "will (i|it|we|you|they)",
    "would (i|it|we|you|they)",
    "might (i|it|we|you|they)",
    "must (i|it|we|you|they)",
    "tell me",
]

QUESTION_BEGINNINGS_PATTERN = re.compile(r"^(but )?" + join_words_in_or_pattern(QUESTION_BEGINNINGS), re.IGNORECASE)


def is_any_question_sentence_in_utterance(annotated_uttr):
    is_question_symbol = "?" in annotated_uttr["text"]
    sentences = re.split(r"[\.\?!]", annotated_uttr["text"])
    is_question_any_sent = any([QUESTION_BEGINNINGS_PATTERN.search(sent.strip()) for sent in sentences])
    if is_question_any_sent or is_question_symbol:
        return True
    return False


WORD_LOVE = r"(like|love|adore|fancy|fond of|fetch|care for|affect|desire|wish|want)"
WORD_HATE = r"(dislike|hate|distaste|loathe|object|bar\b|abominate|disrelish)"
DO_YOU_LOVE_PATTERN = re.compile(r"(do|whether|did|are) you " + WORD_LOVE, re.IGNORECASE)
DO_YOU_HATE_PATTERN = re.compile(r"(do|whether|did|are) you " + WORD_HATE, re.IGNORECASE)
MY_FAVORITE_PATTERN = re.compile(
    r"((is|are|was|were) my (favou?rite|(the )?best|beloved|(a )?loved|well-loved|truelove)|"
    r"my (favou?rite|(the )?best|beloved|(a )?loved|well-loved|truelove)[a-z0-9A-Z \-]* (is|are|was|were))",
    re.IGNORECASE,
)
I_LOVE_PATTERN = re.compile(r"(^|\b)(i|i'm|i am|we|we're|we are) " + WORD_LOVE, re.IGNORECASE)
I_HATE_PATTERN = re.compile(r"(^|\b)(i|i'm|i am|we|we're|we are) " + WORD_HATE, re.IGNORECASE)
WHAT_FAVORITE_PATTERN = re.compile(
    r"(what|which)[a-z0-9A-Z \-]* your (favou?rite|(the )?best|beloved|(a )?loved|well-loved|truelove)", re.IGNORECASE
)
WHAT_LESS_FAVORITE_PATTERN = re.compile(
    r"(what|which)[a-z0-9A-Z \-]* your ((less|least)[- ]favou?rite|(the )?worst|unloved|unlovable)", re.IGNORECASE
)
WHAT_DO_YOU_THINK_PATTERN = re.compile(
    r"(what (do|did|are|were) you (think|believe|recognize|sure|understand|feel|appeal|suppose|imagine|guess|"
    r"fond of|care for|know|thought|mean|reckon|suggest|wonder|expect|say)|"
    r"what (is|are|was|were) your (view|thought|opinion|mind|belief|voice|point|position|feeling|sentiment|"
    r"assessment|judgement|thinking|holding|opining|a say|take))",
    re.IGNORECASE,
)


def get_entities_with_attitudes(annotated_uttr: dict, prev_annotated_uttr: dict):
    entities_with_attitudes = {"like": [], "dislike": []}
    all_entities = get_entities(annotated_uttr, only_named=False, with_labels=False)
    all_prev_entities = get_entities(prev_annotated_uttr, only_named=False, with_labels=False)
    logger.info(f"Consider all curr entities: {all_entities}, and all previous entities: {all_prev_entities}")
    curr_entity = all_entities[0] if all_entities else ""
    prev_entity = all_prev_entities[-1] if all_prev_entities else ""
    curr_uttr_text = annotated_uttr.get("text", "")
    prev_uttr_text = prev_annotated_uttr.get("text", "")
    curr_sentiment = get_sentiment(annotated_uttr, probs=False, default_labels=["neutral"])[0]
    current_first_sentence = (
        annotated_uttr.get("annotations", {}).get("sentseg", {}).get("segments", [curr_uttr_text])[0]
    )

    if "?" in current_first_sentence:
        pass
    elif WHAT_FAVORITE_PATTERN.search(prev_uttr_text):
        # what is your favorite ..? - animals -> `like animals`
        entities_with_attitudes["like"] += [curr_entity]
    elif WHAT_LESS_FAVORITE_PATTERN.search(prev_uttr_text):
        # what is your less favorite ..? - animals -> `dislike animals`
        entities_with_attitudes["dislike"] += [curr_entity]
    elif DO_YOU_LOVE_PATTERN.search(prev_uttr_text):
        if is_no(annotated_uttr):
            # do you love .. animals? - no -> `dislike animals`
            entities_with_attitudes["dislike"] += [prev_entity]
        elif is_yes(annotated_uttr):
            # do you love .. animals? - yes -> `like animals`
            entities_with_attitudes["like"] += [prev_entity]
    elif DO_YOU_HATE_PATTERN.search(prev_uttr_text):
        if is_no(annotated_uttr):
            # do you hate .. animals? - no -> `like animals`
            entities_with_attitudes["like"] += [prev_entity]
        elif is_yes(annotated_uttr):
            # do you hate .. animals? - yes -> `dislike animals`
            entities_with_attitudes["dislike"] += [prev_entity]
    elif I_HATE_PATTERN.search(curr_uttr_text):
        # i hate .. animals -> `dislike animals`
        entities_with_attitudes["dislike"] += [curr_entity]
    elif I_LOVE_PATTERN.search(curr_uttr_text) or MY_FAVORITE_PATTERN.search(curr_uttr_text):
        # i love .. animals -> `like animals`
        entities_with_attitudes["like"] += [curr_entity]
    elif if_chat_about_particular_topic(
        annotated_uttr, prev_annotated_uttr=prev_annotated_uttr, key_words=[curr_entity]
    ):
        # what do you want to chat about? - ANIMALS -> `like animals`
        entities_with_attitudes["like"] += [curr_entity]
    elif if_not_want_to_chat_about_particular_topic(annotated_uttr, prev_annotated_uttr=prev_annotated_uttr):
        # i don't wanna talk about animals -> `dislike animals`
        entities_with_attitudes["dislike"] += [curr_entity]
    elif WHAT_DO_YOU_THINK_PATTERN.search(prev_uttr_text):
        if curr_sentiment == "negative":
            # what do you thank .. animals? - negative -> `dislike animals`
            entities_with_attitudes["dislike"] += [prev_entity]
        elif curr_sentiment == "positive":
            # what do you thank .. animals? - positive -> `like animals`
            entities_with_attitudes["like"] += [prev_entity]

    entities_with_attitudes["like"] = [el for el in entities_with_attitudes["like"] if el]
    entities_with_attitudes["dislike"] = [el for el in entities_with_attitudes["dislike"] if el]
    return entities_with_attitudes


ANY_FRIEND_QUESTION = "Do you have any friends?"
MY_FRIENDS_TEMPLATE = re.compile(r"my \b(friend|buddy|buddies|homie|homey|mate\b)", re.IGNORECASE)
NO_FRIENDS_TEMPLATE = re.compile(
    r"(have )?(not|n't|no) (have )?(got )?(any )?(true |real |sincere )?" r"(friend|buddy|buddies|homie|homey|mate\b)",
    re.IGNORECASE,
)

DFF_WIKI_TEMPLATES = {
    "art": re.compile(r"\b(art(s|work)?|draw(s|ed|ing)?|paint(s|ed|ing)?|meme)(s)?\b", re.IGNORECASE),
    "chill": re.compile(r"\b(chill|rest|relax)", re.IGNORECASE),
    "sleep": re.compile(r"\b(sleep|bedtime|go to bed)", re.IGNORECASE),
    "school": re.compile(r"(school|home work|homework|study)", re.IGNORECASE),
    "work": re.compile(r"\bwork(ed|s|ing)?\b", re.IGNORECASE),
    "family": r"(\bhusband|\bwife|\bspouse|\bfamily|\bkids?\b|\bchild\b|\bchildren"
    r"|\b(grand)?(ma|mom|mother|father|pa|dad|parent|daughters?|sons?|child)\b)",
    "space": re.compile(r"\b((space)(ship|flight)?(s?)|planet(s)?)\b", re.IGNORECASE),
    "friends": re.compile(r"\b(friend|buddy|buddies|homie|homey|mate(s)?\b)", re.IGNORECASE),
    "smartphones": re.compile(r"\b((smart)?phone(s)?|mobile|iphone|ipad|android)\b", re.IGNORECASE),
    "bitcoin": re.compile(r"\b(bitcoin|cryptocurrenc(y|ies))\b", re.IGNORECASE),
    "dinosaurs": re.compile(r"\b(dinosaur)", re.IGNORECASE),
    "robots": re.compile(r"\b(robot(s|ics)?|drone(s)?)\b", re.IGNORECASE),
    "cars": re.compile(r"\b(car(s)?|automobile(s)?|driv(e|ed|es|ing)|auto(s)?)\b", re.IGNORECASE),
    "hiking": re.compile(r"\b(hiking|mountain(s)?)\b", re.IGNORECASE),
    "tiktok": re.compile(r"\btik[ ]?tok\b", re.IGNORECASE),
    "anime": re.compile(r"\banime\b|\bpokemon\b", re.IGNORECASE),
    "love": re.compile(
        r"(\b(fall|fell|fallen|falling) in love\b|m in love\b|\bcrush on\b)",
        re.IGNORECASE,
    ),
    "hobbies": re.compile(r"\b(hobby|hobbies|interests)\b", re.IGNORECASE),
    "politics": re.compile(
        r"\b(politic|democra|republi|liber|president|trump\b|byden\b" r"|authoritarianism|monarch|joe biden|biden\b)",
        re.IGNORECASE,
    ),
}

HEALTH_PROBLEMS = re.compile(
    r"\b(broke|health problem|death|dead\b|died\b|dying\b|ache|disease|illnes|ill\b|sickness|sick\b|shoot|chopped off"
    r"|cough\b|runny nose|bruise|sunburn|backache|headache|stomachache|nausea|dizziness|flu\b|fever\b|pain\b|stroke\b"
    r"|influenza|insomnia|pneumonia|covid\b|coronavirus|cancer|diabetes|diarrhea|Dementia|Paralysis|heart attack"
    r"|allergy|Appendicitis|Asthma|infection|Psoriasis|Vitiligo)",
    re.IGNORECASE,
)

LETS_GET_BACK_TO_TOPIC = [
    "But can we get back on topic, please?",
    "Let's get back on topic.",
    "Let's get back to our topic.",
    "Back on topic,",
]
