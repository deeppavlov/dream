import difflib
import random
import re
from itertools import combinations
import logging
from collections import deque

from nltk import ngrams
from nltk.corpus import wordnet
import nltk

from .sentiment import pick_emoji
from .heuristics import apply_heuristics

logger = logging.getLogger(__name__)

DROP_SPEC_TOKEN = "<DROP_REPLY>"


class ReplyChecker:
    def __init__(self, max_len=10, theshold=0.8, correct_generative=True, split_into_sentences=True):
        self._replies = deque([], maxlen=max_len)
        self._theshold = theshold
        self._info = None
        self._max_len = max_len

        self._correct_generative = correct_generative
        self._split_into_sentences = split_into_sentences

    def _ratio(self, seq1, seq2):
        # todo: only works good for same sequences
        return difflib.SequenceMatcher(None, seq1, seq2).ratio()

    def _sentence_max_coincidence_drop(self, reply):
        history = sum([re.split(r' *[\?\.\!][\'"\)\]]* *', r) for r in self._replies], [])

        split_reply = re.split(r' *[\?\.\!][\'"\)\]]* *', reply)
        punc = list(re.finditer(r' *[\?\.\!][\'"\)\]]* *', reply))

        # ratio = 0
        drop = []

        for i, r in enumerate(split_reply):
            for h in history:
                if h and r:
                    ratio = self._ratio(r, h)
                    if ratio > self._theshold:
                        drop.append(i)

        drop = sorted(set(drop), reverse=True)
        for d in drop:
            split_reply.pop(d)
            punc.pop(d)

        original_text = ""

        for s, m in zip(split_reply, punc):
            original_text += s + m.group()
        if len(split_reply) > len(punc):
            original_text += split_reply[-1]

        return original_text.strip()

    def _max_coincidence(self, reply):
        if not self._replies:
            return None, reply

        if self._split_into_sentences:
            reply = self._sentence_max_coincidence_drop(reply)
            if not reply:
                return 1.0, reply

        mc = max(self._replies, key=lambda x: self._ratio(x, reply))

        ratio = self._ratio(mc, reply)

        return ratio, reply

    def _replace_reply(self, reply, request, info):
        return DROP_SPEC_TOKEN

    @staticmethod
    def _correct_repeated_sentences(text):
        split_text = re.split(r' *[\?\.\!][\'"\)\]]* *', text)
        matches = list(re.finditer(r' *[\?\.\!][\'"\)\]]* *', text))

        drop = []
        for i, j in combinations(range(len(split_text)), 2):
            if split_text[j] and split_text[j] in split_text[i]:
                drop.append(j)
        drop = set(drop)
        drop = sorted(drop, reverse=True)

        for d in drop:
            split_text.pop(d)

            matches.pop(d)

        original_text = ""

        for s, m in zip(split_text, matches):
            original_text += s + m.group()
        if len(split_text) > len(matches):
            original_text += split_text[-1]
        return original_text

    def check_reply(self, reply, request, info):
        log = [reply]
        # log_names = ["IN: ", "RL: ", "RS: "]

        try:
            if self._correct_generative:
                reply = ReplyChecker._correct_repeated_sentences(reply)

            ratio, reply = self._max_coincidence(reply)
            log.append(reply)
            if ratio is not None:
                # ratio = self._ratio(mc, reply)

                if ratio > self._theshold:
                    reply = self._replace_reply(reply, request, info)
                    log.append(reply)

        except IndexError:
            reply = log[0]

        # logger.info('[' + ' | '.join([n + str(v) for n, v in zip(log_names, log) ]) + ']')
        self._replies.append(reply)

        return reply

    def clean(self):
        self._info = None
        self._replies = deque([], maxlen=self._max_len)


def get_syn(seq):
    seq = seq.replace("i ", "I ")

    seq = nltk.pos_tag(nltk.word_tokenize(seq))

    synonyms = {}

    for w, s_p in seq:
        if len(w) < 3:
            continue
        if s_p not in ["VBP", "NN", "NNS"]:
            continue

        pos = wordnet.VERB if s_p == "VBP" else wordnet.NOUN

        s = wordnet.synsets(w, pos=pos)
        for word in s:
            for lemma in word.lemma_names():
                if lemma != w:
                    synonyms[lemma.replace("_", " ")] = w
            break

    if not synonyms:
        return None

    key = random.choice(list(synonyms.keys()))
    return synonyms[key], key


def equal_phrases(phrases):
    matches = {
        " am ": "'m ",
        " are  ": "'re ",
        " have ": "'ve ",
        " has ": "'s ",
        "do not": "don't",
        "does not": "doesn't",
    }

    replasments = []

    for ph in phrases:
        a = ph
        for o, r in matches.items():
            if o in a:
                a = a.replace(o, r)
                break
            if r in a:
                a = a.replace(r, o)
                break

        if a == ph:
            # todo: find synonims
            syn = get_syn(a)
            if syn is None:
                a = a.split(" ")
                a[-2], a[-1] = a[-1], a[-2]
                a = " ".join(a)
            else:
                a = a.replace(syn[0], syn[1])

        replasments.append(a)

    return replasments


def ngram_replacer(info, reply, n=3):
    if info is None:
        return reply

    org_reply = reply

    info = re.split(r' *[\?\.\!][\'"\)\]]* *', info.strip().lower())
    reply = re.split(r' *[\?\.\!][\'"\)\]]* *', reply.strip().lower())

    info = sum([list(ngrams(i.split(), n=n)) for i in info if i], [])
    reply = sum([list(ngrams(r.split(), n=n)) for r in reply if r], [])

    phrases = []

    for i in info:
        for r in reply:
            if i == r:
                phrases.append(" ".join(r))
    logger.info(f"len = {len(phrases)}")

    replasments = equal_phrases(phrases)

    for o, r in zip(phrases, replasments):
        org_reply = org_reply.replace(o, r)

    return org_reply


def replace_repeated_reply(reply, request):
    request = [re.sub(r'[\?\.,\!\'"\)\]]*', "", line.strip().lower()).strip() for line in request]
    _reply = re.sub(r'[\?\.,\!\'"\)\]]*', "", reply.strip().lower()).strip()
    return DROP_SPEC_TOKEN if _reply in request else reply


def postprocess_text(
    reply,
    utterances_histories,
    personality,
    reply_checker: ReplyChecker,
    replace_explicit_repeat=True,
    replace_repeat=True,
    replace_ngram=True,
    heuristic=True,
    emoji_prob=0.3,
    ngram_size=3,
    add_questions=0.3
):

    utterances_histories_str = ". ".join(utterances_histories)
    personality_str = ". ".join(personality)

    if heuristic:
        reply = apply_heuristics(
            reply=reply,
            utterances_histories=utterances_histories,
            personality=personality,
        )
        if not (reply):
            return DROP_SPEC_TOKEN

    if replace_explicit_repeat:
        reply = replace_repeated_reply(reply, utterances_histories)

    if replace_repeat:
        reply = reply_checker.check_reply(reply, utterances_histories_str, personality_str)

    if replace_ngram:
        reply = ngram_replacer(personality, reply, n=ngram_size)

    if random.uniform(0, 1) < emoji_prob and DROP_SPEC_TOKEN != reply:
        reply = " ".join([reply, pick_emoji(reply)])

    return reply
