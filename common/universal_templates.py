from random import choice
import re


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

BOOK_TEMPLATES = ['talk about books', 'do you love reading']

BOOK_CHANGE_PHRASE = "Okay! What would you prefer to discuss? Movies or an interesting fact from Wikipedia?"


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


def join_words_in_or_pattern(words):
    return "(" + "|".join([r'\b%s\b' % word for word in words]) + ")"


def join_sentences_in_or_pattern(sents):
    return "(" + "|".join(sents) + ")"


ARTICLES = r"\s?(\ba\b|\ban\b|\bthe\b|\bsome\b|\bany\b)?\s?"
ANY_WORDS = r"[a-zA-Z0-9 ]*"
ANY_SENTENCES = r"[A-Za-z0-9-!,\?\.’'\"’ ]*"
END = r"([!,\?\.’'\"’]+.*)?$"
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
                                      r"speaking|chatter|chitchat|chit chat)"]
WANT_LIKE = ["want to", "wanna", "wish to", "need to", "desire to", r"(would |'d )?(like|love|dream) to", "going to",
             "gonna", "will", "can", "could", "plan to", "in need to", "demand"]
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
        BEGIN_OF_SENT + TALK_TO_ME + END,
        join_words_in_or_pattern(QUESTION_LIKE) + r"\s?" + TALK_TO_ME + END,
        join_words_in_or_pattern(WANT_LIKE) + r"\s?" + TALK_TO_ME + END,
        join_words_in_or_pattern(START_LIKE) + r"\s?" + TALK_TO_ME + END
    ]))

# --------------- I don't want to talk. / I don't want to talk about that. ------------
COMPILE_NOT_WANT_TO_TALK_ABOUT_IT = re.compile(
    r"(not|n't|\bno\b) " + join_words_in_or_pattern(WANT_LIKE) + r"\s" + join_words_in_or_pattern(TALK_LIKE))

# ----- Let's talk about something. / Can we talk about something? / Talk to me about something. ----
COMPILE_LETS_TALK_ABOUT_SOMETHING = re.compile(join_sentences_in_or_pattern(
    [
        BEGIN_OF_SENT + TALK_TO_ME + r"\s?" + ABOUT_SOMETHING + END,
        join_words_in_or_pattern(QUESTION_LIKE) + r"\s?" + TALK_TO_ME + r"\s?" + ABOUT_SOMETHING + END,
        join_words_in_or_pattern(WANT_LIKE) + r"\s?" + TALK_TO_ME + r"\s?" + ABOUT_SOMETHING + END,
        join_words_in_or_pattern(START_LIKE) + r"\s?" + TALK_TO_ME + r"\s?" + ABOUT_SOMETHING + END,
        r"\bi\s" + join_words_in_or_pattern(WANT_LIKE) + r"\s?" + KNOW + r"\s?" + ABOUT_SOMETHING + END
    ]))

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
    ]))

# ----- Let's talk about TOPIC. / Can we talk about TOPIC? / Talk to me about TOPIC. ----
COMPILE_LETS_TALK_ABOUT_TOPIC = re.compile(join_sentences_in_or_pattern(
    [
        BEGIN_OF_SENT + TALK_TO_ME + SOMETHING_WITH_SPACES + ABOUT_TOPIC + END,
        join_words_in_or_pattern(QUESTION_LIKE) + r"\s?" + TALK_TO_ME + SOMETHING_WITH_SPACES + ABOUT_TOPIC + END,
        join_words_in_or_pattern(WANT_LIKE) + r"\s?" + TALK_TO_ME + SOMETHING_WITH_SPACES + ABOUT_TOPIC + END,
        join_words_in_or_pattern(START_LIKE) + r"\s?" + TALK_TO_ME + SOMETHING_WITH_SPACES + ABOUT_TOPIC + END,
        BEGIN_OF_SENT + "discuss" + r"\s" + ANY_WORDS + END,
        join_words_in_or_pattern(QUESTION_LIKE) + r"\s?" + "discuss" + r"\s" + ANY_WORDS + END,
        join_words_in_or_pattern(WANT_LIKE) + r"\s?" + "discuss" + r"\s" + ANY_WORDS + END,
        join_words_in_or_pattern(START_LIKE) + r"\s?" + "discuss" + r"\s" + ANY_WORDS + END,
        r"\bi\s" + join_words_in_or_pattern(WANT_LIKE) + r"\s?" + KNOW + SOMETHING_WITH_SPACES + ABOUT_TOPIC + END
    ]))

WHAT_TO_TALK_ABOUT = r"what (do|can|could|will|would|are) (you|we|i) " + join_words_in_or_pattern(WANT_LIKE) + \
                     r"\s" + join_words_in_or_pattern(TALK_LIKE) + r"\s" + join_words_in_or_pattern(ABOUT_LIKE) + END
PICK_UP_THE_TOPIC = r"(pick up|choose|select|give)( me)?" + ARTICLES + r"topic" + END
ASK_ME_SOMETHING = r"(ask|tell|say)( me)?" + join_words_in_or_pattern(SOMETHING_LIKE) + END

# ----- What do you want to talk about? / Pick up the topic. / Ask me something. ----
COMPILE_WHAT_TO_TALK_ABOUT = re.compile(join_sentences_in_or_pattern(
    [WHAT_TO_TALK_ABOUT, PICK_UP_THE_TOPIC, ASK_ME_SOMETHING]))

# ----- Something. / Anything. / Nothing. ----
COMPILE_SOMETHING = re.compile(join_sentences_in_or_pattern(
    [join_words_in_or_pattern(SOMETHING_LIKE), join_words_in_or_pattern(DONOTKNOW_LIKE)]) + END)


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
    user_uttr_annotations = annotated_uttr['annotations']
    cobot_dialogacts = set(user_uttr_annotations.get("cobot_dialogact_topics", {}).get("text", {}))
    named_cobot_dialogacts = {"Entertainment_Books", "Entertainment_Movies", "Entertainment_Music"}
    dialogact_met = len(named_cobot_dialogacts & cobot_dialogacts) > 0
    return dialogact_met


def is_switch_topic(annotated_uttr):
    annotations = annotated_uttr.get("annotations", {})
    topic_switch_detected = annotations.get("intent_catcher", {}).get("topic_switching", {}).get("detected", 0) == 1
    intents = annotations.get("cobot_dialogact_intents", {}).get("text", {})
    intent_detected = "Topic_SwitchIntent" in intents
    if intent_detected or topic_switch_detected or if_switch_topic(annotated_uttr["text"].lower()):
        return True
    else:
        return False


def if_choose_topic(uttr, prev_uttr="---"):
    uttr_ = uttr.lower()
    prev_uttr_ = prev_uttr.lower()
    if re.search(COMPILE_SWITCH_TOPIC, uttr_):
        return True
    elif re.search(COMPILE_LETS_TALK_ABOUT_SOMETHING, uttr_):
        return True
    elif re.search(COMPILE_WHAT_TO_TALK_ABOUT, uttr_):
        return True
    elif re.search(COMPILE_WHAT_TO_TALK_ABOUT, prev_uttr_) and \
            re.search(COMPILE_SOMETHING, uttr_):
        return True
    else:
        return False
