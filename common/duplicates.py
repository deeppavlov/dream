from nltk.tokenize import sent_tokenize

from common.news import NEWS_DUPLICATES


ALL_DUPLICATES_SENTS = NEWS_DUPLICATES


def phrase_tokenize(phrases):
    tokenized_phrases = []
    for sents in phrases:
        tokenized_sents = sent_tokenize(sents.lower())
        tokenized_phrases.extend(tokenized_sents)
    return tokenized_phrases


NOT_LOWER_DUPLICATES_SENTS = phrase_tokenize(ALL_DUPLICATES_SENTS)
