import re
import json
import pathlib
import string

from common.books import BOOK_PATTERN
from common.gaming import VIDEO_GAME_WORDS_COMPILED_PATTERN
from common.universal_templates import if_chat_about_particular_topic, \
    if_choose_topic, COMPILE_NOT_WANT_TO_TALK_ABOUT_IT
from common.utils import get_not_used_template
from nltk.tokenize import word_tokenize


GENRES = {"Genre": ["genre"],
          "Action": ["action"],
          "Adult": ["adult", "grown up"],
          "Adventure": ["adventure", "cloak and dagger", "cloak and sword"],
          "Animation": ["animation", "cartoon", 'animated'],
          "Biography": ["biography", "biographies", "biographical"],
          "Comedy": ["comedy", "comedies", "comic", "comical", "funny", "comedian",
                     "humorous", "jocular", "grotesque", "buffo", "entertaining"],
          "Crime": ["crime", "criminal"],
          "Documentary": ["documentary", "documentaries", "doc", "docs", "record"],
          "Drama": ["drama", "dramatic"],
          "Family": ["family", "families"],
          "Fantasy": ["fantasy", "fantasies", "phantasy", "phantasies", "fantastic", "phantastic"],
          "Film-noir": ["film noir"],
          "Game-show": ["game show", "play show", "competition"],
          "History": ["history", "histories", "historical"],
          "Horror": ["horror", "nightmare", "awful", "scaring", "scared", "scary", "scarey",
                     "spooky", "spookies", "eerie", "eery", "uncanny", "uncannies", "fearful"],
          "Music": ["music"],
          "Musical": ["musical"],
          "Mystery": ["mystery", "mysteries", "mystic", "mystical", "mysterious"],
          "News": ["news", "tidings"],
          "Reality-tv": ["reality tv", "reality", "realities", "reality show"],
          "Romance": ["romance", "romantic", "love story", "love stories"],
          "Sci-fi": ["science fiction", "fiction", "sci fi"],
          "Short": ["short"],
          "Sport": ["sport", "sporty", "sports"],
          "Talk-show": ["talk show", 'conversation', "interview", "chat show"],
          "Thriller": ["thriller"],
          "War": ["war movie", "military", "militaries", "martial"],
          "Western": ["western", "west"]
          }

ALL_GENRES = sum(list(GENRES.values()), [])
ALL_GENRES_STR = r"("

for i, genre in enumerate(ALL_GENRES):
    ALL_GENRES_STR += genre
    if i == len(ALL_GENRES) - 1:
        ALL_GENRES_STR += ")"
    else:
        ALL_GENRES_STR += "|"

# all_genres_str looks like:
# '(crime|drama|mystery|thriller|action|romance)' etc


def list_unique_values(dictionary):
    """
    Return all the unique values from `dictionary`'s values lists except `None`
    and `dictionary`'s keys where these values appeared

    Args:
        dictionary: dictionary which values are lists or None

    Returns:
        dict where keys are unique values from `dictionary` and values
        are keys from `dictionary` where these values appeared
    """
    allel = {}

    for keyel, el in zip(dictionary.keys(), dictionary.values()):
        if el is not None:
            for subel in el:
                if subel in allel:
                    allel[subel] += [keyel]
                else:
                    allel[subel] = [keyel]
    return allel


MOVIE_WORDS = r"(movie|film|picture|series|tv[ -]?show|reality[ -]?show|netflix|\btv\b|" \
              r"comedy|comedies|thriller|animation|anime|talk[ -]?show|cartoon|watch)"
MOVIE_PATTERN = re.compile(MOVIE_WORDS, re.IGNORECASE)
YEAR_TEMPLATE = re.compile(r"([0-9][0-9][0-9][0-9])", re.IGNORECASE)

MOVIE_TITLE_QUESTION = re.compile(r"(what|which)[a-zA-Z\- ']+" + MOVIE_WORDS + r"[a-zA-Z\- ']*\?",
                                  re.IGNORECASE)

EXTRA_SPACE_TEMPLATE = re.compile(r"\s\s+")
LETTERS = re.compile(r"[a-zA-Z]+")


def remove_punct_and_articles(s, lowecase=True):
    articles = ['a', "an", 'the']
    if lowecase:
        s = s.lower()
    no_punct = ''.join([c for c in s if c not in string.punctuation])
    no_articles = ' '.join([w for w in word_tokenize(no_punct) if w.lower() not in articles])
    return no_articles


def donot_chat_about_movies(uttr):
    if re.search(COMPILE_NOT_WANT_TO_TALK_ABOUT_IT, uttr.get("text", "").lower()) and \
            re.search(MOVIE_PATTERN, uttr.get("text", "").lower()):
        return True
    else:
        return False


def is_movie_title_question(uttr):
    curr_uttr_is_about_movies = re.search(MOVIE_TITLE_QUESTION, uttr.get("text", ""))
    if curr_uttr_is_about_movies and "do you usually watch movies at home" not in uttr.get("text", ""):
        return True
    else:
        return False


def is_book_question(uttr):
    curr_uttr_is_about_books = re.search(BOOK_PATTERN, uttr.get("text", ""))
    if curr_uttr_is_about_books:
        return True
    else:
        return False


def is_game_question(uttr):
    curr_uttr_is_about_games = re.search(VIDEO_GAME_WORDS_COMPILED_PATTERN, uttr.get("text", ""))
    if curr_uttr_is_about_games:
        return True
    else:
        return False


def is_about_movies(uttr, prev_uttr=None):
    prev_uttr = {} if prev_uttr is None else prev_uttr
    curr_uttr_is_about_movies = re.search(MOVIE_PATTERN, uttr.get("text", "").lower())
    prev_uttr_last_sent = prev_uttr.get("annotations", {}).get("sentseg", {}).get("segments", [""])[-1].lower()
    prev_uttr_is_about_movies = re.search(MOVIE_PATTERN, prev_uttr_last_sent)
    lets_talk_about_movies = if_chat_about_particular_topic(uttr, prev_uttr, compiled_pattern=MOVIE_PATTERN)
    chosed_topic = if_choose_topic(uttr, prev_uttr) and curr_uttr_is_about_movies

    if lets_talk_about_movies or chosed_topic or curr_uttr_is_about_movies or \
            ("?" in prev_uttr_last_sent and prev_uttr_is_about_movies):
        return True
    else:
        return False


def lets_chat_about_movies(uttr, prev_uttr=None):
    prev_uttr = {} if prev_uttr is None else prev_uttr
    curr_uttr_is_about_movies = re.search(MOVIE_PATTERN, uttr.get("text", "").lower())
    lets_talk_about_movies = if_chat_about_particular_topic(uttr, prev_uttr, compiled_pattern=MOVIE_PATTERN)
    chosed_topic = if_choose_topic(uttr, prev_uttr) and curr_uttr_is_about_movies

    if lets_talk_about_movies or chosed_topic or \
            ("?" not in uttr.get("text", "") and "?" in prev_uttr.get("text", "") and curr_uttr_is_about_movies):
        return True
    else:
        return False


with open(pathlib.Path(__file__).resolve().parent.parent.parent / "databases/recommendations.json", "r") as f:
    RECOMMENDATIONS = json.load(f)


def recommend_movie_of_genre(genre, discussed_movie_ids=None):
    discussed_movie_ids = discussed_movie_ids if discussed_movie_ids is not None else []

    # let's convert genre from `criminal` to `Crime` (standard IMDb genre)
    for capitalized_genre in GENRES:
        if genre.lower() in GENRES[capitalized_genre]:
            genre = capitalized_genre

    # randomly pick up not discussed movie
    if RECOMMENDATIONS.get(genre, []):
        # because in RECOMMENDATIONS file imdb ids are started from tt, but in our case we store only digits
        available_ids = [pair[0][2:] for pair in RECOMMENDATIONS[genre]]
        return get_not_used_template(discussed_movie_ids, available_ids, any_if_no_available=False)

    return ""
