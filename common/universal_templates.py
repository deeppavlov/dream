from random import choice
import re

from common.utils import join_words_in_or_pattern, join_sentences_in_or_pattern, get_topics, \
    get_intents, get_sentiment
from common.greeting import GREETING_QUESTIONS

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
    "I'd like to hear your opinion on NP."
]


def opinion_request_question():
    return choice(UNIVERSAL_OPINION_REQUESTS)


FACT_ABOUT_TEMPLATES = ["Here's what I've heard.", "Hmm.. What do I know? Yes, this.", "I recall this.",
                        "You know what?"]


def fact_about_replace():
    return choice(FACT_ABOUT_TEMPLATES)


def nounphrases_questions(nounphrase=None):
    if nounphrase and len(nounphrase) > 0:
        question = choice(NP_OPINION_REQUESTS + UNIVERSAL_OPINION_REQUESTS).replace("NP", nounphrase)
    else:
        question = opinion_request_question()
    return question


ARTICLES = r"\s?(\ba\b|\ban\b|\bthe\b|\bsome\b|\bany\b)?\s?"
ANY_WORDS = r"[a-zA-Z0-9 ]*"
ANY_SENTENCES = r"[A-Za-z0-9-!,\?\.’'\"’ ]*"
END = r"([!,\?\.’'\"’]+.*|$)"
BEGIN_OF_SENT = r"^(.*[!,\?\.’'\"’]+ )?"

ABOUT_LIKE = ["about", "of", "on" + ARTICLES + "topic of"]
QUESTION_LIKE = ["let us", "let's", "lets", "let me", "do we", "do i", "do you",
                 "can we", "can i", "can you", "could we", "could i", "could you",
                 "will we", "will i", "will you", "would we", "would i", "would you"]
START_LIKE = ["start", "begin", "launch", "initiate", "go on", "go ahead", "onset"]
TALK_LIKE = ["talk", "chat", "converse", "discuss", "speak", "tell", "say", "gossip", "commune", "chatter",
             "prattle", "confab", "confabulate", "chin", "talk smack",
             r"(have|hold|carry on|change|make|take|give me|turn on|"
             r"go into)" + ARTICLES + r"(conversation|talk|chat|discussion|converse|dialog|dialogue|"
                                      r"speaking|chatter|chitchat|chit chat)",
             f"tell {ANY_WORDS}"]
WANT_LIKE = ["want to", "wanna", "wish to", "need to", "desire to", r"(would |'d )?(like|love|dream) to", "going to",
             "gonna", "will", "can", "could", "plan to", "in need to", "demand", "want to"]
TO_ME_LIKE = [r"to me( now)?", r"with me( now)?", r"me( now)?", "now"]
SOMETHING_LIKE = ["anything", "something", "nothing", "none", "that", "everything"]
DONOTKNOW_LIKE = [r"(i )?(do not|don't) know", "you (choose|decide|pick up)"]
KNOW_LIKE = ["know", "learn", "find out"]

# talk to me, talk with me, talk, talk with me now, talk now.
TALK_TO_ME = join_words_in_or_pattern(TALK_LIKE) + r"(\s" + join_words_in_or_pattern(TO_ME_LIKE) + r")?"
ABOUT_SOMETHING = join_words_in_or_pattern(ABOUT_LIKE) + r"?\s" + join_words_in_or_pattern(SOMETHING_LIKE)
SOMETHING_WITH_SPACES = r"\s?" + join_words_in_or_pattern(SOMETHING_LIKE) + r"?\s?"
ABOUT_TOPIC = join_words_in_or_pattern(ABOUT_LIKE) + r"\s" + ANY_WORDS
KNOW = join_words_in_or_pattern(KNOW_LIKE)

# --------------- Let's talk. / Can we talk? / Talk to me. ------------
COMPILE_LETS_TALK = re.compile(join_sentences_in_or_pattern(
    [
        TALK_TO_ME + END,
        join_words_in_or_pattern(QUESTION_LIKE) + r"\s?" + TALK_TO_ME + END,
        join_words_in_or_pattern(WANT_LIKE) + r"\s?" + TALK_TO_ME + END,
        join_words_in_or_pattern(START_LIKE) + r"\s?" + TALK_TO_ME + END
    ]),
    re.IGNORECASE)

# --------------- I don't want to talk. / I don't want to talk about that. ------------
COMPILE_NOT_WANT_TO_TALK_ABOUT_IT = re.compile(join_sentences_in_or_pattern(
    [
        r"(not|n't|\bno\b) " + join_words_in_or_pattern(WANT_LIKE),
        r"(not|n't|\bno\b) " + join_words_in_or_pattern(TALK_LIKE),
    ]),
    re.IGNORECASE)

# ----- Let's talk about something. / Can we talk about something? / Talk to me about something. ----
COMPILE_LETS_TALK_ABOUT_SOMETHING = re.compile(join_sentences_in_or_pattern(
    [
        TALK_TO_ME + r"\s?" + ABOUT_SOMETHING + END,
        join_words_in_or_pattern(QUESTION_LIKE) + r"\s?" + TALK_TO_ME + r"\s?" + ABOUT_SOMETHING + END,
        join_words_in_or_pattern(WANT_LIKE) + r"\s?" + TALK_TO_ME + r"\s?" + ABOUT_SOMETHING + END,
        join_words_in_or_pattern(START_LIKE) + r"\s?" + TALK_TO_ME + r"\s?" + ABOUT_SOMETHING + END,
        r"\bi\s" + join_words_in_or_pattern(WANT_LIKE) + r"\s?" + KNOW + r"\s?" + ABOUT_SOMETHING + END
    ]),
    re.IGNORECASE)

# ----- Let's talk about something ELSE. / Can we talk about something ELSE? / Talk to me about something ELSE. ----
# ----- .. switch the topic. / .. next topic. / .. switch topic. / Next. ----
COMPILE_SWITCH_TOPIC = re.compile(join_sentences_in_or_pattern(
    [
        BEGIN_OF_SENT + TALK_TO_ME + r"\s?" + ABOUT_SOMETHING + " else" + END,
        join_words_in_or_pattern(QUESTION_LIKE) + r"\s?" + TALK_TO_ME + r"\s?" + ABOUT_SOMETHING + " else" + END,
        join_words_in_or_pattern(WANT_LIKE) + r"\s?" + TALK_TO_ME + r"\s?" + ABOUT_SOMETHING + " else" + END,
        join_words_in_or_pattern(START_LIKE) + r"\s?" + TALK_TO_ME + r"\s?" + ABOUT_SOMETHING + " else" + END,
        r"(switch|change|next)" + ARTICLES + "topic" + END,
        r"^next" + END,
        r"\bi\s" + join_words_in_or_pattern(WANT_LIKE) + r"\s?" + KNOW + r"\s" + ABOUT_SOMETHING + " else" + END
    ]),
    re.IGNORECASE)

# ----- Let's talk about TOPIC. / Can we talk about TOPIC? / Talk to me about TOPIC. ----
COMPILE_LETS_TALK_ABOUT_TOPIC = re.compile(join_sentences_in_or_pattern(
    [
        TALK_TO_ME + SOMETHING_WITH_SPACES + ABOUT_TOPIC + END,
        join_words_in_or_pattern(QUESTION_LIKE) + r"\s?" + TALK_TO_ME + SOMETHING_WITH_SPACES + ABOUT_TOPIC + END,
        join_words_in_or_pattern(WANT_LIKE) + r"\s?" + TALK_TO_ME + SOMETHING_WITH_SPACES + ABOUT_TOPIC + END,
        join_words_in_or_pattern(START_LIKE) + r"\s?" + TALK_TO_ME + SOMETHING_WITH_SPACES + ABOUT_TOPIC + END,
        BEGIN_OF_SENT + "discuss" + r"\s" + ANY_WORDS + END,
        join_words_in_or_pattern(QUESTION_LIKE) + r"\s?" + "discuss" + r"\s" + ANY_WORDS + END,
        join_words_in_or_pattern(WANT_LIKE) + r"\s?" + "discuss" + r"\s" + ANY_WORDS + END,
        join_words_in_or_pattern(START_LIKE) + r"\s?" + "discuss" + r"\s" + ANY_WORDS + END,
        r"\bi\s" + join_words_in_or_pattern(WANT_LIKE) + r"\s?" + KNOW + SOMETHING_WITH_SPACES + ABOUT_TOPIC + END
    ]),
    re.IGNORECASE)

WHAT_TO_TALK_ABOUT = r"what (do|can|could|will|would|are) (you|we|i) " + join_words_in_or_pattern(WANT_LIKE) + \
                     r"\s" + join_words_in_or_pattern(TALK_LIKE) + r"\s" + join_words_in_or_pattern(ABOUT_LIKE) + END
PICK_UP_THE_TOPIC = r"(pick up|choose|select|give)( me)?" + ARTICLES + r"topic" + END
ASK_ME_SOMETHING = r"(ask|tell|say)( me)?" + join_words_in_or_pattern(SOMETHING_LIKE) + END
WHATS_ON_YOUR_MIND = r"what('s| is) on your mind"

# ----- What do you want to talk about? / Pick up the topic. / Ask me something. ----
COMPILE_WHAT_TO_TALK_ABOUT = re.compile(join_sentences_in_or_pattern(
    [WHAT_TO_TALK_ABOUT, PICK_UP_THE_TOPIC, ASK_ME_SOMETHING, WHATS_ON_YOUR_MIND]),
    re.IGNORECASE)

# ----- Something. / Anything. / Nothing. ----
COMPILE_SOMETHING = re.compile(join_sentences_in_or_pattern(
    [join_words_in_or_pattern(SOMETHING_LIKE), join_words_in_or_pattern(DONOTKNOW_LIKE)]) + END,
    re.IGNORECASE)


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
    cobot_dialogacts = set(get_topics(annotated_uttr, which="cobot_dialogact_topics"))
    named_cobot_dialogacts = {"Entertainment_Books", "Entertainment_Movies", "Entertainment_Music"}
    dialogact_met = len(named_cobot_dialogacts & cobot_dialogacts) > 0
    return dialogact_met


def is_switch_topic(annotated_uttr):
    topic_switch_detected = "topic_switching" in get_intents(annotated_uttr, which="intent_catcher")

    if topic_switch_detected or if_switch_topic(annotated_uttr["text"].lower()):
        return True
    else:
        return False


def if_choose_topic(annotated_uttr, prev_annotated_uttr={}):
    """Dialog context implies that the next utterances can pick up a topic:
        - annotated_uttr asks to switch topic
        - annotated_uttr asks "what do you want to talk about?"
        - annotated_uttr asks "let's talk about something (else)"
        - prev_annotated_uttr asks "what do you want to talk about?", and annotated_uttr says something/anything.
    """
    uttr_ = annotated_uttr.get('text', "").lower()
    prev_uttr_ = prev_annotated_uttr.get('text', '--').lower()
    chat_about_intent = 'lets_chat_about' in get_intents(annotated_uttr, probs=False, which='intent_catcher')
    user_asks_what_to_talk_about = re.search(COMPILE_WHAT_TO_TALK_ABOUT, uttr_)
    # user ask to "talk about something"
    smth1 = re.search(COMPILE_LETS_TALK_ABOUT_SOMETHING, uttr_) or (chat_about_intent and re.search(
        COMPILE_SOMETHING, uttr_))
    # bot asks "what user wants to talk about", and user answers "something"
    prev_chat_about_intent = 'lets_chat_about' in get_intents(prev_annotated_uttr, probs=False, which='intent_catcher')
    prev_uttr_asks_what_topic = prev_chat_about_intent or re.search(COMPILE_WHAT_TO_TALK_ABOUT, prev_uttr_)
    smth2 = prev_uttr_asks_what_topic and re.search(COMPILE_SOMETHING, uttr_)

    switch_topic = is_switch_topic(annotated_uttr)
    if switch_topic or user_asks_what_to_talk_about or (smth1 or smth2):
        return True
    return False


def if_chat_about_particular_topic(annotated_uttr, prev_annotated_uttr={}, key_words=[], compiled_pattern=r""):
    """Dialog context implies that the last utterances chooses particular conversational topic:
        - annotated_uttr asks "let's talk about PARTICULAR-TOPIC"
        - prev_annotated_uttr asks "what do you want to talk about?", and annotated_uttr says PARTICULAR-TOPIC.
        - prev_annotated_uttr asks "what are your interests?", and annotated_uttr says PARTICULAR-TOPIC.
    """
    uttr_ = annotated_uttr.get('text', "").lower()
    prev_uttr_ = prev_annotated_uttr.get('text', '--').lower()

    # current uttr is lets talk about blabla
    chat_about_intent = 'lets_chat_about' in get_intents(annotated_uttr, probs=False, which='intent_catcher')
    chat_about = chat_about_intent or if_lets_chat_about_topic(uttr_)

    # prev uttr is what do you want to talk about?
    greeting_question_texts = [question.lower() for t in GREETING_QUESTIONS for question in GREETING_QUESTIONS[t]]
    prev_was_greeting = any([greeting_question in prev_uttr_ for greeting_question in greeting_question_texts])
    prev_chat_about_intent = 'lets_chat_about' in get_intents(prev_annotated_uttr, probs=False, which='intent_catcher')
    prev_what_to_talk_about_regexp = re.search(COMPILE_WHAT_TO_TALK_ABOUT, prev_uttr_)
    prev_what_to_chat_about = prev_was_greeting or prev_chat_about_intent or prev_what_to_talk_about_regexp

    switch_topic = if_choose_topic(annotated_uttr, prev_annotated_uttr)
    not_want = re.search(COMPILE_NOT_WANT_TO_TALK_ABOUT_IT, uttr_)
    if not_want or switch_topic:
        return False
    elif prev_what_to_chat_about or chat_about:
        if key_words:
            if any([word in uttr_ for word in key_words]):
                return True
            else:
                return False
        elif compiled_pattern:
            if re.search(compiled_pattern, uttr_):
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
    cond1 = 'tell_me_more' in intents
    cond2 = re.search(more_details_pattern, annotated_uttr['text'])
    return cond1 or cond2


QUESTION_BEGINNINGS = QUESTION_LIKE + [
    r"what'?s?", "when", "where", "which", r"who'?s?", "whom", "whose", r"how'?s?", "why", "whether",
    "do (i|we|you)", "does (it|he|she)", "have (i|we|you)", "has (it|he|she)",
    "can (i|it|we|you)", "could (i|it|we|you)", "shall (i|we|you)", "should (i|it|we|you)",
    "will (i|it|we|you)", "would (i|it|we|you)", "might (i|it|we|you)", "must (i|it|we|you)",
    "tell me"
]

QUESTION_BEGINNINGS_PATTERN = re.compile(r"^" + join_words_in_or_pattern(QUESTION_BEGINNINGS), re.IGNORECASE)


def is_any_question_sentence_in_utterance(annotated_uttr):
    is_question_symbol = "?" in annotated_uttr["text"]
    sentences = re.split(r'[\.\?!]', annotated_uttr["text"])
    is_question_any_sent = any([QUESTION_BEGINNINGS_PATTERN.search(sent.strip()) for sent in sentences])
    if is_question_any_sent or is_question_symbol:
        return True
    return False
