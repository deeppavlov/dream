import itertools
import json
import logging
import random
import re
import sentry_sdk
from datetime import datetime
from os import getenv
import _pickle as cPickle
import pathlib

from common.books import QUESTIONS_ABOUT_BOOKS, about_book
from common.utils import is_opinion_request, get_intents
from common.link import link_to
from common.utils import entity_to_label, get_raw_entity_names_from_annotations
from common.universal_templates import is_switch_topic, NOT_LIKE_PATTERN
from common.custom_requests import request_triples_wikidata, request_entities_entitylinking

sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

USE_CACHE = True

FAVORITE_PATTERN = r"(favorite|loved|beloved|fondling|best|most interesting)"
CHRISTIANITY_PATTERN = r"(bibla\b|bible\b|bibel\b)"

GENRE_DICT = {
    "memoir": "memoir books",
    "memoir autobiography": "memoir books",
    "history biography": "biography books",
    "science technology": "technology books",
    "debut novel": "debut novel books",
    "graphic novels comics": "comics",
    "picture": "picture books",
    "romance": "romance books",
    "non-fiction": "non-fiction books",
    "food cook": "culinary books",
    "poetry": "poetry books",
    "childrens": "children's literature",
    "mystery thriller": "thriller books",
    "horror": "horror stories",
    "humour": "funny stories",
    "fantasy": "fantasy books",
    "science fiction": "science fiction books",
    "historical fiction": "historical fiction books",
    "fiction": "fiction",
}
GENRE_PHRASES = json.load(open("genre_phrases.json", "r"))[0]

SKILLS_TO_LINK = [
    "news_api_skill",
    "dff_movie_skill",
    "game_cooperative_skill",
    "dff_travel_skill",
    "dff_animals_skill",
    "dff_sport_skill",
    "dff_food_skill",
    "dff_music_skill",
]

book_banned_words_file = pathlib.Path(__file__).parent / "book_banned_words.txt"
book_banned_words = set([line.strip() for line in book_banned_words_file.read_text().split("\n") if line.strip()])
book_query_dict = cPickle.load(open("/global_data/book_query_dict.pkl", "rb"))

AUTHOR_WIKI_TYPES = ["Q36180", "Q18814623", "Q482980", "Q4853732", "Q6625963"]
BOOK_WIKI_TYPES = ["Q571", "Q7725634", "Q1667921", "Q277759", "Q8261", "Q47461344"]
MOVIE_WIKI_TYPES = ["Q11424", "Q24856", "Q202866"]

QA_SERVICE_URL = getenv("COBOT_QA_SERVICE_URL")
API_KEY = getenv("COBOT_API_KEY")
kbqa_files = ["inverted_index_eng.pickle", "entities_list.pickle", "wiki_eng_q_to_name.pickle", "who_entities.pickle"]


# if any([kbqa_file not in os.listdir(os.getcwd()) for kbqa_file in kbqa_files]):
#    with tarfile.open('../global_data/wikidata_eng/wiki_eng_files.tar.gz', "r:gz") as tar_ref:
#        tar_ref.extractall(os.getcwd())
# logger.info('Creating linker')
# linker = entity_linking.KBEntityLinker(load_path=os.getcwd(), save_path=os.getcwd(),
#                                       inverted_index_filename="inverted_index_eng.pickle",
#                                       entities_list_filename="entities_list.pickle",
#                                       q2name_filename="wiki_eng_q_to_name.pickle",
#                                       who_entities_filename="who_entities.pickle")


def was_question_about_book(annotated_utterance):
    if isinstance(annotated_utterance, list):
        return any([was_question_about_book(j) for j in annotated_utterance])
    return "?" in annotated_utterance.get("annotations", {}).get("sentseg", {}).get("punct_sent", "") and about_book(
        annotated_utterance
    )


def is_request_about_book_detected(annotated_user_phrase):
    # TODO: nothing of this is a request of the fact!!!
    cond1 = "have you read " in annotated_user_phrase["text"].lower()
    cond2 = is_opinion_request(annotated_user_phrase) and about_book(annotated_user_phrase)
    cond3 = "?" in annotated_user_phrase["text"] and about_book(annotated_user_phrase)
    # removed cond4 due to the bug in information_request_detected
    # cond4 = information_request_detected(annotated_user_phrase)
    return cond1 or cond2 or cond3  # or cond4


WHAT_ABOUT_PATTERN = re.compile(r"what (it is|is it|is this book) about", re.IGNORECASE)


def what_is_book_about_request(annotated_user_phrase):
    return re.search(WHAT_ABOUT_PATTERN, annotated_user_phrase["text"])


def what_is_book_about(book):
    fact = ""
    logger.info(f"Requesting for {book}")
    if isinstance(book, str):
        if is_wikidata_entity(book):
            plain_books = [book]
        else:
            plain_books, _ = request_entities_entitylinking(book, types=BOOK_WIKI_TYPES)
            logger.info(f"After request {plain_books}")
        if plain_books:
            plain_book = plain_books[0]
            subjects = request_triples_wikidata("find_object", [(plain_book, "P921", "forw")], query_dict={})[0]
            if subjects:
                fact = f"{fact}The main subject of this book is {entity_to_label(subjects[0])}."
            locations = request_triples_wikidata("find_object", [(plain_book, "P840", "forw")], query_dict={})[0]
            if len(locations) > 1:
                fact = f"{fact} Apart from other locations,"
            if locations:
                fact = f"{fact} The action of this book takes place in {entity_to_label(locations[0])}."
            if not subjects or not locations:
                characters = request_triples_wikidata("find_object", [(plain_book, "P674", "forw")], query_dict={})[0]
                if characters:
                    fact = f"{fact} One of the main characters of this book is {entity_to_label(characters[0])}."
    logger.info(f"Final fact {fact}")
    return fact


def get_genre(user_phrase, return_name=False):
    if any([j in user_phrase for j in ["food", "cook", "kitchen"]]):
        genre = "food cook"
    elif any([j in user_phrase for j in ["child", "kid"]]):
        genre = "childrens"
    elif any([j in user_phrase for j in ["poetry", "poesy", "verse", "rhyme", "rime"]]):
        genre = "poetry"
    elif any([j in user_phrase for j in ["mystery", "thriller"]]):
        genre = "mystery thriller"
    elif any([j in user_phrase for j in ["horror"]]):
        genre = "horror"
    elif any([j in user_phrase for j in ["humor", "funny", "laugh", "comics"]]):
        genre = "humour"
    elif any([j in user_phrase for j in ["fantasy"]]):
        genre = "fantasy"
    elif any([j in user_phrase for j in ["nonfiction", "non-fiction"]]):
        genre = "non-fiction"
    elif any([j in user_phrase for j in ["romance", "romantic", "love"]]):
        genre = "romance"
    elif any([j in user_phrase for j in ["picture"]]):
        genre = "picture"
    elif any([j in user_phrase for j in ["comics", "graphic"]]):
        genre = "graphic novels comics"
    elif any([j in user_phrase for j in ["debut"]]):
        genre = "debut novel"
    elif any([j in user_phrase for j in ["technolog", "scientific"]]):
        genre = "science technology"
    elif any([j in user_phrase for j in [" biograph"]]):
        genre = "history biography"
    elif any([j in user_phrase for j in ["memoir", "autobiography"]]):
        genre = "memoir autobiography"
    elif any([j in user_phrase for j in ["sci-fi", "science fiction"]]):
        genre = "science fiction"
    elif any([j in user_phrase for j in ["history", "historic"]]):
        genre = "historical fiction"
    elif any([j in user_phrase for j in ["fiction", " all", "any"]]):
        genre = "fiction"
    else:
        return None
    if return_name:
        return GENRE_DICT[genre]
    else:
        return genre


genres_regexp = f"({'|'.join(GENRE_DICT.keys())})"
do_you_love_regexp = "(do you (love|like|enjoy)|what do you think)"

favorite_genre_template = re.compile(r"(favourite|favorite|best|suggest|recommend) book genre", re.IGNORECASE)
user_favorite_genre_template = re.compile(r"my (favourite|favorite) book genre", re.IGNORECASE)
favorite_book_template = re.compile(r"(favourite|favorite|best|suggest|recommend) book", re.IGNORECASE)
user_favorite_book_template = re.compile(r"my (favourite|favorite) book", re.IGNORECASE)

asked_genre_template = re.compile(rf"{do_you_love_regexp} {genres_regexp}", re.IGNORECASE)


def my_favorite(annotated_user_phrase):
    if re.search(user_favorite_genre_template, annotated_user_phrase["text"]):
        return "genre"
    elif re.search(user_favorite_book_template, annotated_user_phrase["text"]):
        return "book"
    else:
        return None


def fav_genre_request_detected(annotated_user_phrase):
    return re.search(favorite_genre_template, annotated_user_phrase["text"])


def asked_about_genre(annotated_user_phrase):
    return re.search(asked_genre_template, annotated_user_phrase["text"])


def fact_about_book(annotated_user_phrase):
    logger.debug("fact about")
    logger.debug(annotated_user_phrase)
    plain_bookname, _ = get_name(annotated_user_phrase, "book", return_plain=True)
    movie_name, movie_author = get_name(annotated_user_phrase, "movie")
    if not movie_name:
        logger.debug("Getting a fact about bookname")
        if plain_bookname:
            bookname = entity_to_label(plain_bookname)
            reply = what_is_book_about(bookname)
        else:
            reply = ""
    else:
        reply = f"I enjoyed watching the film {movie_name} based on this book, which was directed by {movie_author}. "
    return reply


def is_previous_was_book_skill(dialog):
    return len(dialog["bot_utterances"]) >= 1 and dialog["bot_utterances"][-1]["active_skill"] == "book_skill"


christianity_template = re.compile(CHRISTIANITY_PATTERN, re.IGNORECASE)


def bible_request(annotated_uttr):
    return re.search(christianity_template, annotated_uttr["text"])


def just_mentioned(annotated_phrase, book):
    return book and book.lower() in annotated_phrase["text"].lower()


def get_author(plain_entity, return_plain=False, mode="book"):
    # Input bookname output author name
    logger.info(f"Calling get_author for {plain_entity}")
    logger.debug(f"Search author with entity {plain_entity.upper()}")
    if mode == "book":
        author_list = request_triples_wikidata(
            "find_object",
            [(plain_entity.upper(), "P50", "forw"), (plain_entity.upper(), "P800", "backw")],
            query_dict=book_query_dict,
        )
    else:
        author_list = request_triples_wikidata("find_object", [(plain_entity.upper(), "P57", "forw")], query_dict={})
    logger.info(f"Author list received {author_list}")
    author_list = list(itertools.chain.from_iterable(author_list))
    author_list = list(set(author_list))
    author_list = [x[x.find("Q") :] for x in author_list]  # to unify representations
    sorted_author_list = sorted(author_list, key=lambda x: int(x[1:]))  # Sort entities by frequency
    if not sorted_author_list:
        return None
    author_entity = sorted_author_list[0]
    if return_plain:
        logger.info(f"Answer {author_entity}")
        return author_entity
    else:
        if is_wikidata_entity(author_entity):
            author_name = entity_to_label(author_entity)
            logger.info(f"Answer for get_author {author_name}")
            return author_name
        else:
            logger.warning(f"Wrong entity {author_entity}")
            return None


def get_published_year(book_entity):
    global wikidata
    # print('Entity '+book_entity)
    logger.info(f"Calling get_published_year for {book_entity}")
    # assert type(book_entity) == str and book_entity[0] == 'Q'
    book_entity = book_entity.strip()
    published_year = None
    published_year_list = request_triples_wikidata(
        "find_object", [(book_entity, "P577", "forw")], query_dict=book_query_dict
    )
    logger.info(f"Received {published_year_list}")
    if isinstance(published_year_list, str):
        published_year = published_year_list
    else:
        while published_year_list and type(published_year_list[0]) == list:
            # Support different formats of wikiparser output
            published_year_list = published_year_list[0]
        if published_year_list and type(published_year_list[0]) == str:
            published_year = published_year_list[0]
        else:
            published_year = ""
    year_candidates = re.findall(r"[\d]{3,4}", published_year)
    if year_candidates:
        try:
            published_year = int(year_candidates[0])
            assert published_year
        except Exception:
            # sentry_sdk.capture_exception(e)
            logger.exception(f"Could not obtain published year from {published_year_list}")
    logger.info(f"Answer for get_published_year {published_year}")
    return published_year


def book_or_author(bookname, stopwords):
    return bookname and not all([len(word) < 5 or word in stopwords for word in bookname.split(" ")])


def process_year(publication_year):
    is_timeout = publication_year in [[], [[]]]
    if is_timeout:
        return None
    start_ind, n_years_ago = None, None
    for i in range(len(publication_year)):
        if publication_year[i] in "0123456789" and not start_ind:
            start_ind = i
    if start_ind:
        publication_year = publication_year[start_ind : start_ind + 4]
        n_years_ago = datetime.now().year - int(publication_year)
    else:
        logger.warning(f"Wrong output {publication_year} no n_years_ago")
    return n_years_ago


def get_name(
    annotated_phrase, mode="author", bookyear=False, return_plain=False, stopwords=book_banned_words
):  # it was wikidata_process_entities
    """
    Processes list of entity candidates(entity_list) using wikidata
    Entities are NOT wikidata objects!!!
    Returns a single name of book or author if it exists.
    P106 - instance of
    Q36180 - author
    Q18814623 - autobiographer
    P31 - instance of
    Q571 - book
    Q7725634, Q1667921, Q277759 - book serie
    """
    plain_entity, found_entity, n_years_ago, attribute, film_director = None, None, None, None, None
    try:
        all_found_entities = get_raw_entity_names_from_annotations(annotated_phrase["annotations"])
        if not all_found_entities:
            logger.warning(f'Entities not found in {annotated_phrase["annotations"].get("entity_linking", {})}')
            return None, None
        logger.info(f"Found entities in annotations {all_found_entities}")
        if mode == "author":
            types = AUTHOR_WIKI_TYPES
        elif mode == "book":
            types = BOOK_WIKI_TYPES
        elif mode == "movie":
            types = MOVIE_WIKI_TYPES
        else:
            raise Exception(f"Wrong mode: {mode}")
        n_years_ago = None
        wp_annotations = annotated_phrase["annotations"].get("wiki_parser", {})
        if isinstance(wp_annotations, list):
            wp_annotations = wp_annotations[0]
        toiterate_dict = wp_annotations.get("topic_skill_entities_info", {})
        for key in wp_annotations.get("entities_info", {}):
            if key not in toiterate_dict:
                toiterate_dict[key] = wp_annotations["entities_info"][key]
        keys = sorted(toiterate_dict, key=lambda x: -len(str(toiterate_dict[x])))
        #  logger.debug(toiterate_dict)
        #  To discern omonyms ( e.g serbian old king Stephen and Stephen King)
        #  we sort by the length of wikidata dict -
        # the more popular is the person the more info about it we have and the sooner we get it
        toiterate_dict = {key: toiterate_dict[key] for key in keys}
        for entity in toiterate_dict:
            found_types = []
            logger.debug(f"Examine {entity}")
            logger.debug(found_types)
            if "types_2hop" in toiterate_dict[entity]:
                found_types.extend([j[0] for j in toiterate_dict[entity]["types_2hop"] if j[0] not in found_types])
            logger.debug(found_types)
            if "instance of" in toiterate_dict[entity]:
                found_types.extend([j[0] for j in toiterate_dict[entity]["instance of"] if j[0] not in found_types])
            logger.debug(found_types)
            if not any([j in types for j in found_types]):
                logger.warning(f"Querying wikidata for {entity}")
                found_types = []
                for type_ in types:
                    request_answer = request_triples_wikidata(
                        "check_triplet", [(entity, "P31", "forw")], query_dict=book_query_dict
                    )
                    if isinstance(request_answer, list) and request_answer[0]:
                        found_types.append(type_)
            logger.debug(f"Found types {found_types}")
            logger.debug(f"Interception {[k for k in types if k in found_types]}")
            if any([j in types for j in found_types]) and book_or_author(entity, stopwords):
                logger.debug(f"{mode} found")
                found_entity = entity
                if "plain_entity" not in toiterate_dict[entity]:
                    logger.warning(f"No plain_entity found in annotation for {entity}")
                    plain_entities, _ = request_entities_entitylinking(entity, types=types, confidence_threshold=0.05)
                    plain_entity = plain_entities[0]
                else:
                    plain_entity = toiterate_dict[entity]["plain_entity"]
                if mode == "book":
                    if "publication date" in toiterate_dict[entity]:
                        publication_year = toiterate_dict[entity]["publication date"][0][0]
                    else:
                        logger.warning("No publication date found in annotation for {entity}")
                        publication_year = get_published_year(plain_entity)
                    n_years_ago = process_year(publication_year)
                elif mode == "movie":
                    if "film director" in toiterate_dict[entity]:
                        film_director = toiterate_dict[entity]["film producer"][0][0]
                    else:
                        film_director = get_author(plain_entity, mode="movie")
                elif mode == "author":  # to get rid of abbreviations such as J R R Tolkien
                    found_entity = " ".join([k for k in found_entity.split(" ") if len(k) > 1])
                break
            else:
                logger.info(f"No interception with {types}")
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
    entity = plain_entity if return_plain else found_entity
    attribute = film_director if mode == "movie" else n_years_ago
    logger.info(f"Answer for get_name {entity} {attribute}")
    return entity, attribute


def get_booklist(plain_author_name):
    book_list = request_triples_wikidata(
        "find_object",
        [(plain_author_name, "P800", "forw"), (plain_author_name, "P50", "backw")],
        query_dict=book_query_dict,
    )
    book_list = list(itertools.chain.from_iterable(book_list))
    book_list = list(set(book_list))
    book_list = [x[x.find("Q") :] for x in book_list if x]  # to unify representations
    book_list = sorted(book_list, key=lambda x: int(x[1:]))
    return book_list


def best_plain_book_by_author(plain_author_name, default_phrase, plain_last_bookname=None, top_n_best_books=1):
    logger.debug(f"Calling best_plain_book_by_author for {plain_author_name} {plain_last_bookname}")
    # best books
    last_bookname = "NO_BOOK"
    try:
        book_list = get_booklist(plain_author_name)
        if plain_last_bookname is not None:
            book_list = [j for j in book_list if plain_last_bookname not in j]
            last_bookname = entity_to_label(plain_last_bookname)
        logger.debug("List of returned books - processed")
        logger.debug(book_list)
        best_bookname = default_phrase  # default value
        if book_list:
            filtered_bookname_list = []
            for book in book_list:
                logger.debug(f"{last_bookname.lower()} {entity_to_label(book).lower()}")
                if len(filtered_bookname_list) < top_n_best_books:
                    if last_bookname.lower() not in entity_to_label(book).lower():
                        filtered_bookname_list.append(book)
                        if len(filtered_bookname_list) >= top_n_best_books:
                            break
            if len(filtered_bookname_list) > 0:
                best_bookname = random.choice(filtered_bookname_list)
        logger.debug(f"Answer for best_plain_book_by_author {best_bookname}")
        return best_bookname
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(f"Error processing {book_list}")
        return default_phrase


def entities_to_labels(entities_list):
    return [entity_to_label(k) for k in entities_list]


def author_genres(plain_author_name):
    plain_genres = request_triples_wikidata(
        "find_object", [(plain_author_name, "P136", "forw")], query_dict=book_query_dict
    )
    return entities_to_labels(plain_genres)


def get_plain_genres(plain_bookname):
    plain_genres = request_triples_wikidata(
        "find_object", [(plain_bookname, "P136", "forw")], query_dict=book_query_dict
    )
    MAX_DEPTH = 5
    for _ in range(MAX_DEPTH):
        if plain_genres and isinstance(plain_genres[0], list):
            plain_genres = plain_genres[0]
    logger.debug(f"Plain_genres {plain_genres}")
    return plain_genres


def genre_of_book(plain_bookname):
    logger.info(f"Call genre_of_book for {plain_bookname}")
    plain_genres = get_plain_genres(plain_bookname)
    if plain_genres:
        plain_genres = sorted(plain_genres, key=lambda x: int(x[1:]))
        genre = entity_to_label(plain_genres[0])
        if genre[0] not in ["aeoiyu"]:
            genre = f"a {genre}"
        else:
            genre = f"an {genre}"
        return genre
    else:
        return ""


def parse_author_best_book(annotated_phrase, default_phrase=None):
    global author_names
    logger.debug(f'Calling parse_author_best_book for {annotated_phrase["text"]}')
    annotated_phrase["text"] = annotated_phrase["text"].lower()
    if re.search(r"\bis\b", annotated_phrase["text"]):
        annotated_phrase["text"] = annotated_phrase["text"].split(" is ")[1]
    plain_bookname, _ = get_name(annotated_phrase, "book", return_plain=True)
    if plain_bookname is None:
        logger.debug(f"Getting plain author")
        plain_author, _ = get_name(annotated_phrase, "author", return_plain=True)
    else:
        logger.debug(f"Processing bookname in get_author {plain_bookname}")
        plain_author = get_author(plain_bookname, return_plain=True, mode="book")
        logger.debug(f"Plain_author {plain_author}")
    if plain_author:
        logger.debug(f"author detected: {plain_author} bookname {plain_bookname}")
        plain_book = best_plain_book_by_author(
            plain_author_name=plain_author, plain_last_bookname=plain_bookname, default_phrase=default_phrase
        )
        logger.debug(f"Answer for parse_author_best_book is {(plain_book, plain_author)}")
        return plain_book, plain_author
    else:
        logger.debug("No author found")
        return default_phrase, None


dontlike_request = re.compile(
    r"(not like|not want to talk|not want to hear|not concerned about|"
    r"over the books|no books|stop talking about|no more books|i do not read|"
    r"not want to listen|not know how to read)",
    re.IGNORECASE,
)


def dontlike_books(last_utterance):
    last_uttr_text = last_utterance["text"].lower()
    last_uttr_text = re.sub("wanna", "want to", last_uttr_text, re.IGNORECASE)
    last_uttr_text = re.sub("don't'", "do not", last_uttr_text, re.IGNORECASE)
    if re.search(dontlike_request, last_uttr_text) or re.search(NOT_LIKE_PATTERN, last_uttr_text):
        return True
    return False


dontknow_template = re.compile(r"(n't|not) (know|remember)", re.IGNORECASE)


def dontknow_books(annotated_uttr):
    return re.search(dontknow_template, annotated_uttr["text"])


suggest_template = re.compile(r"(suggest|recommend)", re.IGNORECASE)


def get_not_given_question_about_books(used_phrases):
    not_asked_questions = set(QUESTIONS_ABOUT_BOOKS).difference(set(used_phrases))
    if len(not_asked_questions):
        # choose not used question about books
        reply = random.choice(list(not_asked_questions))
    else:
        # choose any question about books
        reply = random.choice(QUESTIONS_ABOUT_BOOKS)
    return reply


def is_side_intent(annotated_uttr):
    # One of the intents which are side intents for
    side_intent_list = [
        "don't understand",
        "what_can_you_do",
        "what_is_your_job",
        "what_is_your_name",
        "what_time",
        "where_are_you_from",
        "who_made_you",
    ]
    intents = get_intents(annotated_uttr, which="intent_catcher", probs=False)
    for side_intent in side_intent_list:
        if side_intent in intents:
            return True
    return False


def is_stop(annotated_uttr):
    # if exit intent, the skill will not be turned on anyway
    intents = get_intents(annotated_uttr, which="intent_catcher", probs=False)
    exit_intent = "exit" in intents
    switch_intent = is_switch_topic(annotated_uttr)
    stop_or_no_intent = "stop" in annotated_uttr["text"].lower()
    return exit_intent or switch_intent or stop_or_no_intent


def tell_about_genre_book(bookname, bookreads_data):
    reply = None
    logger.debug(f"Detected name {bookname} in last_bot_phrase")
    for genre in bookreads_data:
        for book_ in bookreads_data[genre]:
            if book_.get("title", "") == bookname:
                logger.debug(f"Returning phrase for book of genre {genre}")
                reply = book_.get("description", "")
                return reply
    return reply


def get_movie_answer(annotated_user_phrase, human_attributes):
    reply = ""
    movie_name, movie_author = get_name(annotated_user_phrase, "movie")
    if movie_name and movie_author:
        reply = (
            f"I enjoyed watching the film {movie_name} based on this book," f"which was directed by {movie_author}. "
        )
        reply += link_to(["dff_movie_skill"], human_attributes)["phrase"]
    return reply


def exit_skill(reply, human_attr, SKILLS_TO_LINK=SKILLS_TO_LINK):
    # link = link_to(SKILLS_TO_LINK, human_attr)['phrase']
    exit_phrase = "We have been talking about books for a fair amount of time. " f"Let's talk about something else."
    if not any([exit_phrase in phrase for phrase in human_attr["book_skill"]["used_phrases"]]):
        reply = f"{reply} {exit_phrase}"
    else:
        reply = f""
    return reply


PUBLISHED_YEAR_TEMPLATE = re.compile(r"(it )? was (that book )?(written|published|out)", re.IGNORECASE)


def published_year_request(annotated_user_phrase):
    return re.search(PUBLISHED_YEAR_TEMPLATE, annotated_user_phrase["text"])


HAVENT_READ_TEMPLATE = re.compile(r"(haven't|have not|didn't|did not) (read)?", re.IGNORECASE)


def havent_read(annotated_user_phrase):
    return re.search(HAVENT_READ_TEMPLATE, annotated_user_phrase["text"])


IS_WIKIDATA_TEMPLATE = re.compile(r"Q[0-9]+", re.IGNORECASE)


def is_wikidata_entity(plain_book):
    if isinstance(plain_book, str):
        if re.fullmatch(IS_WIKIDATA_TEMPLATE, plain_book):
            return True
    return False


LOVE_READING_TEMPLATE = re.compile(r"i (do )?(like|love|prefer) (book|read)", re.IGNORECASE)


def if_loves_reading(annotated_user_phrase):
    return re.search(LOVE_READING_TEMPLATE, annotated_user_phrase["text"])


BY_TEMPLATE = re.compile(r"\bby ([a-zA-Z ]+)", re.IGNORECASE)


def find_by(annotated_user_phrase):
    found_by = re.search(BY_TEMPLATE, annotated_user_phrase["text"])
    if found_by:
        answer = found_by.group()[3:]
        return answer
    else:
        return ""


WHAT_TEMPLATE = re.compile(r"what (is|it)", re.IGNORECASE)


def asked_what(annotated_user_phrase):
    return re.search(WHAT_TEMPLATE, annotated_user_phrase["text"])


def set_favourite(human_attr, index, FAVOURITE_BOOK_ATTRS, FAVOURITE_BOOK_ANSWERS):
    plain_book, n_years_ago, book, author = FAVOURITE_BOOK_ATTRS[index]
    fav_book_phrases = FAVOURITE_BOOK_ANSWERS[index]
    human_attr["book_skill"]["plain_book"] = plain_book
    human_attr["book_skill"]["n_years_ago"] = n_years_ago
    human_attr["book_skill"]["book"] = book
    human_attr["book_skill"]["author"] = author
    human_attr["book_skill"]["fav_book_phrases"] = fav_book_phrases
    return human_attr
