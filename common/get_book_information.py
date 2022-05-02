import re
import json

with open('common/books_info.json', 'r') as f:
    books_info = json.load(f)
    books = list(books_info.keys())

TELL_ABOUT_BOOK_PATTERN = re.compile(r"\btell .* about (" + ("|".join(books) + ")"), re.IGNORECASE)

TELL_BOOK_GENRE_PATTERN = re.compile(r"\bwhat.* genre of (" + ("|".join(books) + ")"), re.IGNORECASE)

TELL_BOOK_AUTHOR_PATTERN = re.compile(r"\bwho (wrote|is the author of) (" + ("|".join(books) + ")"), re.IGNORECASE)

TELL_BOOK_DESCRIPTION_PATTERN = re.compile(r"\bwhat (" + ("|".join(books) + ") ") + "is about", re.IGNORECASE)
