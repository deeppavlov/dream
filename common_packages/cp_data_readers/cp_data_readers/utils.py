import json
import re
from collections import Counter
from itertools import chain
from string import punctuation

import nltk

# Use Dockerfile to download punkt in '/usr/local/nltk_data'
# by ``` RUN python -c "import nltk; nltk.download('punkt')" ```

RUSSIAN_SUBJECTS = ["история", "обществознание", "литература", "русский язык"]

# ===========================
# Punctuation utils
# ===========================

PUNCTUATION = punctuation + "«»—"


def is_apostrophe(sent, i):
    return (0 < i < len(sent) - 1) and sent[i] == "'" and sent[i + 1][0].islower()


def is_punctuation(word):
    return all(x in PUNCTUATION for x in word)


# ===========================
# Prochtenie utils
# ===========================


def clear_text(text):
    return text.lower().replace(" ", "")


def find_closest_type(raw_type, submap):
    max_proximity = 0
    closest_standard_type = ""
    clear_raw_type = clear_text(raw_type)
    for standard_raw_type in submap.keys():
        current_proximity = common_characters_counter(raw_type, standard_raw_type)
        if (current_proximity > max_proximity and current_proximity > 0.8) or common_substring(
            clear_raw_type, standard_raw_type, (len(clear_raw_type) + len(standard_raw_type)) // 4
        ):
            max_proximity = current_proximity
            closest_standard_type = submap[standard_raw_type]
    return closest_standard_type


def common_characters_counter(str1, str2):
    dict1 = Counter(str1)
    dict2 = Counter(str2)
    commonDict = dict1 & dict2

    return 2 * sum(list(commonDict.values())) / (len(str1) + len(str2))


def common_substring(str1, str2, n):
    if str1[0] != str2[0] and str2[1] == ".":
        return []
    str1_substrings = [str1[i : i + n] for i in range(len(str1) - n)]
    str2_substrings = [str2[i : i + n] for i in range(len(str2) - n)]
    common_substrings = list(set(str1_substrings) & set(str2_substrings))
    return common_substrings


def find_standard_type(raw_type, submap):
    standard_raw_types = list(submap.keys())
    clean_type = clear_text(raw_type)
    if clean_type == "":
        return ""
    if clean_type not in standard_raw_types:
        for standard_raw_type in standard_raw_types:
            if (clean_type in standard_raw_type or standard_raw_type in clean_type) and len(clean_type) > 2:
                return submap[standard_raw_type]
        closest_standard_type = find_closest_type(clean_type, submap)
        return closest_standard_type
    else:
        return submap[clean_type]


# ===========================
# Sentence tokenization utils
# ===========================


def find_offsets(text, segments, start=0, append_end=False):
    """
    Finds the beginnings of segments in text
    """
    offsets = []
    for segment in segments:
        offset = text.find(segment, start)
        if offset >= 0:
            start = offset + len(segment)
        else:
            raise ValueError(f"segment '{segment}' does not occur in text '{text}' from position {start}")
        offsets.append(offset)
    if append_end:
        offsets.append(len(text))
    return offsets


def postprocess_sentence_tokenization(sents):
    """
    Fixes some errors in `ru_sent_tokenize` tokenization.
    However, it changes offsets in text, therefore error spans should also be fixed when using this function.
    """
    answer = []
    for i, sent in enumerate(sents):
        sent = sent.strip()
        if len(sent) == 0:
            continue
        if i > 0 and sent[0].islower() and sents[i - 1].endswith("."):
            answer[-1] += " " + sent
        else:
            answer.append(sent)
    return answer


def sent_tokenize(text, tokenizer=None):
    if tokenizer is None:
        tokenizer = nltk.tokenize.sent_tokenize
    matches = list(re.finditer("(?<!\.[A-ZА-ЯЁ])[\.?!](?=[A-ZА-ЯЁ][^.])", text))
    starts = [0] + [elem.start() + 1 for elem in matches] + [len(text)]
    segments = [text[start:end] for start, end in zip(starts[:-1], starts[1:])]
    answer = list(chain.from_iterable(map(tokenizer, segments)))
    return answer


def _word_tokenize(
    text,
    tokenizer=None,
    start_offset=0,
    postprocess_hyphens=True,
    postprocess_apostrophs=True,
    postprocess_long_punctuation=True,
):
    tokenizer = tokenizer or nltk.tokenize.WordPunctTokenizer()
    words = tokenizer.tokenize(text)
    word_offsets = find_offsets(text, words, start=start_offset)
    if postprocess_hyphens:
        new_word_indexes, i = [], 0
        while i < len(words):
            if i < len(words) - 3 and words[i + 1] == "-":  #  and words[i+2].islower():
                if "".join(words[i : i + 2]) == text[word_offsets[i] : word_offsets[i + 2]]:
                    new_word_indexes.append(i)
                    i += 3
                    continue
            new_word_indexes.append(i)
            i += 1
        new_word_indexes.append(len(words))
        words = ["".join(words[start:end]) for start, end in zip(new_word_indexes[:-1], new_word_indexes[1:])]
        word_offsets = [word_offsets[i] for i in new_word_indexes[:-1]]
    if postprocess_long_punctuation:
        new_word_offsets, new_words = [], []
        for i, word in enumerate(words):
            if len(word) > 1 and not all(x == "." for x in word) and is_punctuation(word):
                new_words.extend(word)
                new_word_offsets.extend(word_offsets[i] + j for j in range(len(word)))
            else:
                new_words.append(word)
                new_word_offsets.append(word_offsets[i])
        words, word_offsets = new_words, new_word_offsets
    if postprocess_apostrophs:
        new_word_indexes, i = [], 0
        while i < len(words):
            new_word_indexes.append(i)
            if i + 1 < len(words) and is_apostrophe(words, i + 1):
                if len(words[i + 2]) <= 2:
                    i += 3
                else:
                    i += 2
            else:
                i += 1
        new_word_indexes.append(len(words))
        words = ["".join(words[i:j]) for i, j in zip(new_word_indexes[:-1], new_word_indexes[1:])]
        word_offsets = [word_offsets[i] for i in new_word_indexes[:-1]]
    return words, word_offsets


def _parse_to_sentences(text, tokenizer=None, sentence_tokenizer=None, postprocess_hyphens=True):
    transl_table = {ord(a): ord(b) for a, b in zip("`‘’´“”«»–-", "''''\"\"\"\"--")}
    text = text.translate(transl_table)
    tokenizer = tokenizer or nltk.tokenize.WordPunctTokenizer()
    paragraphs = text.split("\n")
    sentences, offsets = [], []
    paragraph_start = 0
    for paragraph in paragraphs:
        sents = sent_tokenize(paragraph.strip(), tokenizer=sentence_tokenizer)
        sent_offsets = find_offsets(text, sents, start=paragraph_start)
        # we calculate offsets in the whole document to match ProChtenie annotation
        curr_sentences, curr_offsets = [], []
        for i, sent in enumerate(sents):
            words, word_offsets = _word_tokenize(sent)
            curr_sentences.append({"text": sent, "words": words})
            # we need absolute word offsets, not relative ones
            curr_offsets.append([sent_offsets[i] + offset for offset in word_offsets])
        sentences.append(curr_sentences)
        offsets.append(curr_offsets)
        paragraph_start += len(paragraph) + 1
    while not (sentences[-1]):
        sentences.pop()
        offsets.pop()

    return sentences, offsets


# ===========================
# Json utils
# ===========================


def open_json(path):
    try:
        with open(path, "r") as f:
            data = json.load(f)
        return data
    except Exception:
        return None
