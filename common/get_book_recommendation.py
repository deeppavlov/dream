import re

BOOKS_PATTERN = re.compile(r"\b(harry potter|war and peace|1984)", re.IGNORECASE)

APPRECIATION_PATTERN = re.compile(r"\b(my favorite|my fav|my favourite|i love|i like)", re.IGNORECASE)

GENRES_PATTERN = re.compile(r"\b(fantasy|historical|dystopian)", re.IGNORECASE)