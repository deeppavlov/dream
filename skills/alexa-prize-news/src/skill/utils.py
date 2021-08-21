import re
from collections import defaultdict
from typing import List, Optional, Union, Tuple

from Levenshtein.StringMatcher import StringMatcher

from src.consts import NUM_NEWS_TO_PRINT, MIN_LEVENSHTEIN_DISTANCE


def clean_message(message):
    words = ["give", "tell", "me", "would", "like", "hear", "news", "about", "topic"]
    message = re.split("[^a-z]+", message)
    message = [w for w in message if w not in words]
    message = " ".join(message)
    return message


def parse_entity(ner_index: dict, message: str) -> str:
    words = re.split("[^a-zA-Z]+", message)
    num = len(words) + 1
    entity = None
    for i in range(num):
        for j in range(i):
            candidate = " ".join(words[j : num - i + j])
            if candidate.lower() in ner_index:
                entity = candidate
                break
        if entity is not None:
            break
    # entity = find_any_tag(context.raw_message, ["PER", "ORG", "LOC", "GPE"])
    return entity


def score_news_by_entities(ner_index: dict, entities: List[str], num=NUM_NEWS_TO_PRINT) -> List[int]:
    scores = defaultdict(int)
    for e in entities:
        e = e.lower()
        if e in ner_index:
            for news_id in ner_index[e]:
                scores[news_id] += 1

    scores = sorted(scores, key=lambda x: scores[x], reverse=True)
    return scores[:num]


def score_news(model, message: str) -> Tuple[List[Union[str, int]], List[Union[str, float]]]:
    prediction = model([message])
    indices = prediction[0][0][:NUM_NEWS_TO_PRINT]
    scores = prediction[1][0][:NUM_NEWS_TO_PRINT]
    return indices, scores


def parse_topic(topics: List[str], message: str) -> Optional[str]:
    message = re.split("[^a-z]+", message)
    topics = sorted(topics, key=len, reverse=True)
    topics = [t.split() for t in topics]

    scores = []
    for topic in topics:
        score = get_match_score(topic, message)
        score += get_match_score(get_paired(topic), get_paired(message))
        scores.append((topic, score))

    if scores:
        topic, score = max(scores, key=lambda x: x[1])
        if score > 0.4:
            extra_words_num = (1 - get_match_score(message, topic)) * len(message)
            if extra_words_num < 2:
                return " ".join(topic)
    return None


def get_paired(words: List[str]) -> List[str]:
    """
    Pair each word with the next one with a white space.
    :param words: a list of words
    :return: a list of strings, where each one is a concatenation of two neighboring original words.
    """
    if len(words) > 1:
        return [w1 + " " + w2 for w1, w2 in zip(words[:-1], words[1:])]
    return []


def get_match_score(phrase: List[str], words: List[str]) -> float:
    """
    Return a match score between two lists of words.
    Score = len([1 for p in phrase for w in words if p == w]) / len(phrase), where == is Levenshtein-based.
    The min_distance is normalized, such that MIN_LEVENSHTEIN_DISTANCE errors are allowed for 4 chars in a word.
    :param phrase: a list of words to evaluate
    :param words: a list of words to find
    :return:
    """
    score = 0
    for p in phrase:
        matcher = StringMatcher(seq1=p)
        for w in words:
            matcher.set_seq2(w)
            match_distance = matcher.distance()
            min_distance = MIN_LEVENSHTEIN_DISTANCE * (len(p) + len(w)) / 8
            if match_distance < min_distance:
                score += 0.5 * (2 - match_distance / min_distance) / len(phrase)
    return score


def is_list_of_strings(obj):
    if obj and isinstance(obj, list):
        return all(isinstance(s, str) for s in obj)
    return False
