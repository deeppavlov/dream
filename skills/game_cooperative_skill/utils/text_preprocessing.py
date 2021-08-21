import re


spaces_pat = re.compile(r"\s+")
special_symb_pat = re.compile(r"[^a-zа-я0-9 ]")


def clean_text(text):
    return special_symb_pat.sub("", spaces_pat.sub(" ", text.lower().replace("\n", " "))).strip()
