import re

BOOKS_PATTERN = re.compile(r"\b(harry potter|war and peace|1984)", re.IGNORECASE)

APPRECIATION_PATTERN = re.compile(r"\b(my favorite|my fav|my favourite|i love|i like)", re.IGNORECASE)

GENRES_PATTERN = re.compile(r"\b(fantasy|historical|dystopian)", re.IGNORECASE)

RECOMMEND_BOOK_PATTERN = re.compile(r"\b(recommend a book|recommend me a book|what book would you suggest|recommend a dystopian novel|recommend me a dystopian novel|recommend a historical novel|recommend me a historical novel|recommend a fantasy novel|recommend me a fantasy novel)", re.IGNORECASE)