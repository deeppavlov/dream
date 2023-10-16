def join_words_in_or_pattern(words):
    return r"(" + r"|".join([r"\b%s\b" % word for word in words]) + r")"


def join_word_beginnings_in_or_pattern(words):
    return r"(" + r"|".join([r"\b%s" % word for word in words]) + r")"


def join_sentences_in_or_pattern(sents):
    return r"(" + r"|".join(sents) + r")"
