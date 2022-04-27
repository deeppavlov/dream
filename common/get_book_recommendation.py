import re
import json

with open('common/genre2books.json', 'r') as f:
    genre2books = json.load(f)
    genres = list(genre2books.keys())

with open('common/book2genre.json', 'r') as f:
    book2genre = json.load(f)
    books = list(book2genre.keys())[:500]

BOOKS_PATTERN = re.compile(r"|".join(books), re.IGNORECASE)

APPRECIATION_PATTERN = re.compile(r"\b(my favorite|my fav|my favourite|i love|i like)", re.IGNORECASE)

GENRES_PATTERN = re.compile(r"|".join(genres), re.IGNORECASE)

RECOMMEND_BOOK_PATTERN = re.compile(r"\b(recommend a book|recommend me a book|what book would you suggest to read|what book should i read|what book would you recommend)", re.IGNORECASE)

BOOKS_TOPIC_PATTERN = re.compile(r"\b(discuss books|speak about books)", re.IGNORECASE)