import re

spaces_pat = re.compile(r"\s+")
special_symb_pat = re.compile(r"[^A-Za-z0-9 ]")


def clear_text(text):
    text = special_symb_pat.sub("", spaces_pat.sub(" ", text.lower().replace("\n", " "))).strip()
    text = text.replace("\u2019", "'")
    return text
