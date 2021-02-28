import itertools
import json
import logging
import os
import random
import re
import requests
import sentry_sdk
import time
import zipfile
import _pickle as cPickle
from datetime import datetime
from os import getenv

from common.books import QUESTIONS_ABOUT_BOOKS, about_book
from common.universal_templates import is_switch_topic, if_lets_chat
from common.utils import is_opinion_request, is_no, get_sentiment

sentry_sdk.init(getenv('SENTRY_DSN'))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)

USE_CACHE = True
EL_CONF_THRES = 0.6

NOT_LIKE_PATTERN = r"(dislike|not like|not want|not love|not prefer|hate|n't like|" \
                   r"not into|not fond|not crazy|not appriciate|n't appriciate|" \
                   r"disintrested|not for you|not for me|not a big fan|loathe|not stand|n't stand|" \
                   r"not much of fan|not read)"
LIKE_PATTERN = r"(like|love|prefer|adore|enjoy|fond of|passionate of|fan of|interested in|" \
               r"into|for you|for me)"
FAVORITE_PATTERN = r"(favorite|loved|beloved|fondling|best|most interesting)"

GENRE_PHRASES = json.load(open('genre_phrases.json', 'r'))[0]
DEBUG_MODE = False
if DEBUG_MODE:
    API_KEY = 'QFPxaMUoPi5qcax2FBt9D6Y6vAgLRBbn56TW1iO3'
    QA_SERVICE_URL = 'https://06421kpunk.execute-api.us-east-1.amazonaws.com/prod/qa/v1/answer'
    WIKIDATA_URL = 'http://0.0.0.0:8077/model'
    ENTITY_LINKING_URL = 'http://0.0.0.0:8075/model'
else:
    QA_SERVICE_URL = getenv('COBOT_QA_SERVICE_URL')
    WIKIDATA_URL = getenv("WIKIDATA_URL")
    ENTITY_LINKING_URL = getenv("ENTITY_LINKING_URL")
    API_KEY = getenv('COBOT_API_KEY')

kbqa_files = ['inverted_index_eng.pickle',
              'entities_list.pickle',
              'wiki_eng_q_to_name.pickle',
              'who_entities.pickle']
if "author_namesbooks.pkl" not in os.listdir(os.getcwd()):
    with zipfile.ZipFile("../global_data/author_namesbooks.zip", "r") as zip_ref:
        zip_ref.extractall(os.getcwd())
author_names, author_books = cPickle.load(open('author_namesbooks.pkl', 'rb'))
stopwords = [j.strip() for j in open('stopwords.txt', 'r').readlines()]
stopwords = set(stopwords)
# if any([kbqa_file not in os.listdir(os.getcwd()) for kbqa_file in kbqa_files]):
#    with tarfile.open('../global_data/wikidata_eng/wiki_eng_files.tar.gz', "r:gz") as tar_ref:
#        tar_ref.extractall(os.getcwd())
# logger.info('Creating linker')
# linker = entity_linking.KBEntityLinker(load_path=os.getcwd(), save_path=os.getcwd(),
#                                       inverted_index_filename="inverted_index_eng.pickle",
#                                       entities_list_filename="entities_list.pickle",
#                                       q2name_filename="wiki_eng_q_to_name.pickle",
#                                       who_entities_filename="who_entities.pickle")

logger.info('Loading cached wikidata file')
wikidata = cPickle.load(open('wikidata_data.pkl', 'rb'))
logger.info('All files successfully created')


def was_question_about_book(annotated_utterance):
    if isinstance(annotated_utterance, list):
        return any([was_question_about_book(j) for j in annotated_utterance])
    return '?' in annotated_utterance.get("annotations", {}).get("sentseg", {}).get(
        "punct_sent", "") and about_book(annotated_utterance)


def is_stop(annotated_phrase):
    # if exit intent, the skill will not be turned on anyway
    exit_intent = annotated_phrase['annotations']['intent_catcher'].get('exit', {}).get('detected') == 1
    switch_intent = is_switch_topic(annotated_phrase)
    stop_or_no_intent = 'stop' in annotated_phrase['text'].lower() or is_no(annotated_phrase)
    if exit_intent or switch_intent or stop_or_no_intent:
        return True
    return False


def side_intent(annotated_phrase):
    side_intent_list = ["don't understand", 'what_can_you_do', 'what_is_your_job', 'what_is_your_name',
                        'what_time', 'where_are_you_from', 'who_made_you']
    for side_intent in side_intent_list:
        if annotated_phrase['annotations']['intent_catcher'].get(side_intent, {}).get('detected') == 1:
            return True
        return False


def is_negative(annotated_phrase):
    sentiment = get_sentiment(annotated_phrase, probs=False)[0]
    return sentiment in ["negative", "very_negative"]


def is_positive(annotated_phrase):
    sentiment = get_sentiment(annotated_phrase, probs=False)[0]
    return sentiment in ["positive", "very_positive"]


more_details_pattern = re.compile(r"(\bmore\b|detail)", re.IGNORECASE)


def tell_me_more(annotated_phrase):
    cond1 = annotated_phrase['annotations']['intent_catcher'].get('tell_me_more', {}).get('detected') == 1
    cond2 = if_lets_chat(annotated_phrase['text']) and re.search(more_details_pattern, annotated_phrase['text'])
    return cond1 or cond2


def is_request_about_book_detected(annotated_user_phrase):
    # TODO: nothing of this is a request of the fact!!!
    cond1 = 'have you read ' in annotated_user_phrase['text'].lower()
    cond2 = is_opinion_request(annotated_user_phrase) and about_book(annotated_user_phrase)
    cond3 = "?" in annotated_user_phrase['text'] and about_book(annotated_user_phrase)
    # removed cond4 due to the bug in information_request_detected
    # cond4 = information_request_detected(annotated_user_phrase)
    return cond1 or cond2 or cond3  # or cond4


def get_genre(user_phrase, return_name=False):
    if any([j in user_phrase for j in ['food', 'cook', 'kitchen']]):
        genre = 'food cook'
    elif any([j in user_phrase for j in ['child', 'kid']]):
        genre = 'childrens'
    elif any([j in user_phrase for j in ['poetry', 'poesy', 'verse', 'rhyme', 'rime']]):
        genre = 'poetry'
    elif any([j in user_phrase for j in ['mystery', 'thriller']]):
        genre = 'mystery thriller'
    elif any([j in user_phrase for j in ['horror']]):
        genre = 'horror'
    elif any([j in user_phrase for j in ['humor', 'funny', 'laugh', 'comics']]):
        genre = 'humour'
    elif any([j in user_phrase for j in ['fantasy']]):
        genre = 'fantasy'
    elif any([j in user_phrase for j in ['nonfiction', 'non-fiction']]):
        genre = 'non-fiction'
    elif any([j in user_phrase for j in ['romance', 'romantic', 'love']]):
        genre = 'romance'
    elif any([j in user_phrase for j in ['picture']]):
        genre = 'picture'
    elif any([j in user_phrase for j in ['comics', 'graphic']]):
        genre = 'graphic novels comics'
    elif any([j in user_phrase for j in ['debut']]):
        genre = 'debut novel'
    elif any([j in user_phrase for j in ['technolog', 'scientific']]):
        genre = 'science technology'
    elif any([j in user_phrase for j in [' biograph']]):
        genre = 'history biography'
    elif any([j in user_phrase for j in ['memoir', 'autobiography']]):
        genre = 'memoir autobiography'
    elif any([j in user_phrase for j in ['sci-fi', 'science fiction']]):
        genre = 'science fiction'
    elif any([j in user_phrase for j in ['history', 'historic']]):
        genre = 'historical fiction'
    elif 'fiction' in user_phrase:
        genre = 'fiction'
    else:
        return None
    if return_name:
        genre_dict = {'memoir autobiography': 'memoir books',
                      'history biography': 'biography books',
                      'science technology': 'technology books',
                      'debut novel': 'debut novel books',
                      'graphic novels comics': 'comics',
                      'picture': 'picture books',
                      'romance': 'romance books',
                      'non-fiction': 'non-fiction books',
                      'food cook': 'culinary books',
                      'poetry': 'poetry books',
                      'childrens': "children's literature",
                      'mystery thriller': 'thriller books',
                      'horror': 'horror stories',
                      'humour': 'funny stories',
                      'fantasy': 'fantasy books',
                      'science fiction': 'science fiction books',
                      'historical fiction': 'historical fiction books',
                      'fiction': 'fiction'
                      }
        return genre_dict[genre]
    else:
        return genre


favorite_genre_template = re.compile(r"(favourite|favorite|best|suggest|recommend) book genre", re.IGNORECASE)
favorite_book_template = re.compile(r"(favourite|favorite|best|suggest|recommend) book", re.IGNORECASE)


def fav_genre_request_detected(annotated_user_phrase):
    return re.search(favorite_genre_template, annotated_user_phrase["text"])


def fav_book_request_detected(annotated_user_phrase):
    return re.search(favorite_book_template, annotated_user_phrase["text"])


def get_answer(phrase):
    logger.debug('Getting COBOT anwer for phrase')
    logger.debug(phrase)
    try:
        headers = {'Content-Type': 'application/json;charset=utf-8', 'x-api-key': API_KEY}
        answer = requests.request(url=QA_SERVICE_URL, headers=headers, timeout=1,
                                  data=json.dumps({'question': phrase}), method='POST').json()
        return_value = answer['response']
        logger.debug(answer['response'])
        logger.debug(f'Response obtained: {return_value}')
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
        logger.debug('Response not obtained')
        return_value = ""

    return return_value


def fact_about_book(annotated_user_phrase):
    logger.debug('fact about')
    logger.debug(annotated_user_phrase)
    bookname, _ = get_name(annotated_user_phrase, 'book')
    logger.debug('Getting a fact about bookname')
    reply = get_answer(f'fact about "{bookname}"')
    return reply


def get_triples(parser_info, queries):
    logger.debug(f"Calling get_triples, parser_info {parser_info}, queries {queries}")
    try:
        t = time.time()
        response = [[]]
        resp = requests.post(WIKIDATA_URL,
                             json={"query": queries, "parser_info": parser_info},
                             timeout=0.5)
        if resp.status_code == 200:
            response = [elem[0] for elem in resp.json()]
        else:
            logger.debug("Could not access wiki parser")
        exec_time = round(time.time() - t, 2)
        logger.debug(f'Response obtained with exec time {exec_time}')
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
        response = []

    return response


def request_entities(entity):
    logger.debug(f'Calling request_entities for {entity}')
    try:
        # assert type(entity) == str
        t = time.time()
        used_types = ["Q36180",  # writer
                      "Q49757",  # novelist
                      "Q214917",  # playwright
                      "Q1930187",  # journalist
                      "Q6625963",  # novelist
                      "Q28389",  # screenwriter
                      "Q571",  # book
                      "Q7725634",  # literary work
                      "Q1667921"  # novel series
                      ]
        response = requests.post(ENTITY_LINKING_URL,
                                 json={"entity_substr": [[entity]],
                                       "template_found": [""],
                                       "context": [""],
                                       "entity_types": [[used_types]]},
                                 timeout=1).json()
        exec_time = round(time.time() - t, 2)
        logger.debug(f'Response is {response} with exec time {exec_time}')

        entities = response[0][0][0]
        probs = response[0][1][0]
        if len(entities) == len(probs) and entities:
            entities_with_conf = [(entity, conf) for entity, conf in zip(entities, probs) if conf > EL_CONF_THRES]
            if entities_with_conf:
                entities, probs = zip(*entities_with_conf)
            else:
                entities, probs = [], []
        # assert len(entities) == len(probs)
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
        entities = []
        probs = []

    return entities, probs


def is_previous_was_book_skill(dialog):
    return len(dialog['bot_utterances']) >= 1 and dialog["bot_utterances"][-1]["active_skill"] == 'book_skill'


def get_entities(annotated_phrase):
    named_entities = [annotated_phrase['text']]
    if 'annotations' in annotated_phrase:
        for tmp in annotated_phrase['annotations']['ner']:
            if len(tmp) > 0 and 'text' in tmp[0] and tmp[0]['text'] not in named_entities:
                named_entities.append(tmp[0]['text'])
        for nounphrase in annotated_phrase['annotations'].get("cobot_nounphrases", []):
            if nounphrase not in named_entities:
                named_entities.append(nounphrase)
    for i in range(len(named_entities) - 1, -1, -1):
        ent_words = named_entities[i].split(' ')
        if all([len(ent_word) < 5 or ent_word in stopwords for ent_word in ent_words]):
            del named_entities[i]  # word is either too short or stopword
    return named_entities


def preprocess_entities(named_entities):
    logger.debug(f'Calling preprocess_entities for {str(named_entities)}')
    # auxillary function from get_name aimed at entites processing
    processed_entities = []
    banned_entities = ['tik tok', 'minecraft', 'the days']
    try:
        for entity in named_entities:
            if 'when' in entity and 'was first published' in entity:
                entity = entity.split('when')[1].split('was first published')[0]
            for pattern in ['read was', 'book is', 'book was']:
                if pattern in entity:
                    entity = entity.split(pattern)[1]
            if entity not in banned_entities:
                processed_entities.append(entity)
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
    return processed_entities


def get_name(annotated_phrase, mode='author', bookyear=True, return_plain=False):
    # Annotated phrase: str or dict
    # Getting author name or book name
    # Returning entity name and(on request) when the book was published
    if type(annotated_phrase) == str:
        annotated_phrase = {'text': annotated_phrase}
    logger.debug(f'Calling get_name for: Mode {mode} Phrase: {annotated_phrase["text"]}')
    if return_plain:
        logger.debug("With plain")
    named_entities = get_entities(annotated_phrase)
    processed_entities = preprocess_entities(named_entities)
    logger.debug(f'named entities: {named_entities}')
    logger.debug(f'processed entities: {processed_entities}')

    entityname, n_years = wikidata_process_entities(processed_entities, mode=mode, bookyear=bookyear,
                                                    return_plain=return_plain)
    logger.debug(f'Answer {entityname} {n_years}')
    return entityname, n_years


def who_wrote_book(book, return_plain=False):
    # Input bookname output author name
    logger.debug(f'Calling who_wrote_book for {book}')
    if book[0].upper() == 'Q' and all([j in '1234567890' for j in book[1:]]):  # it is plain
        plain_book_entity = book
    else:
        plain_book_entity, _ = wikidata_process_entities(book, mode='book',
                                                         bookyear=False, return_plain=True)
    logger.debug(f'Search author with entity {plain_book_entity.upper()}')
    author_list = []
    if book in wikidata['who_wrote_book']:
        author_list = wikidata['who_wrote_book'][book]
    else:
        # It means that we don't have author in cache. No reason for exception!
        logger.info(f'No author found in cache for {book}')
        author_list = get_triples(["find_object", "find_object"], [(plain_book_entity.upper(), "P50", "forw"),
                                                                   (plain_book_entity.upper(), "P800", "backw")])
        author_list = list(itertools.chain.from_iterable(author_list))
        author_list = list(set(author_list))
        logger.debug(f'Author list received {author_list}')
        author_list = [x[x.find('Q'):] for x in author_list]  # to unify representations
    sorted_author_list = sorted(author_list, key=lambda x: int(x[1:]))  # Sort entities by frequency
    author_entity = sorted_author_list[0]
    if return_plain:
        logger.debug(f'Answer {author_entity}')
        return author_entity
    else:
        author_name = entity_to_label(author_entity)
        logger.debug(f'Answer {author_name}')
        return author_name


def get_wikidata_entities(entity_list):
    logger.debug(f'Calling get_wikidata_entities for {entity_list}')
    if type(entity_list) == str:
        entity_list = [entity_list]
    answer_entities = []  # All found wikidata entitites
    found_wikidata_entities = []
    entity_list = [j.lower() for j in entity_list]
    for entity in entity_list:  # We search for wikidata entities in each entity provided
        if entity in wikidata['entities']:
            found_wikidata_entities = [wikidata['entities'][entity]]
        else:
            wikidata_entities, probs = request_entities(entity)
            logger.debug(wikidata_entities[:2])
            logger.debug(probs[:2])
            if len(probs) > 0:
                max_prob = max(probs)
                found_wikidata_entities = [entity for i, entity in enumerate(wikidata_entities)
                                           if probs[i] == max_prob]
            else:
                found_wikidata_entities = []
        answer_entities = answer_entities + found_wikidata_entities
    logger.debug(f'Answer {answer_entities}')
    return answer_entities


def get_published_year(book_entity):
    global wikidata
    # print('Entity '+book_entity)
    logger.debug(f'Calling get_published_year for {book_entity}')
    # assert type(book_entity) == str and book_entity[0] == 'Q'
    book_entity = book_entity.strip()
    published_year = ""
    if book_entity in wikidata['published_year']:
        published_year = wikidata['published_year'][book_entity]
    else:
        published_year = get_triples(["find_object"], [(book_entity, "P577", "forw")])[0]
        try:
            logger.debug(f'Answer list {published_year}')
            published_year = re.findall(r"[\d]{3,4}", published_year[0])[0]
            logger.debug(f'Answer {published_year}')
        except Exception as e:
            sentry_sdk.capture_exception(e)
            logger.exception(f'Could not obtain published year from {published_year}')
    return published_year


def entity_to_label(entity):
    logger.debug(f'Calling entity_to_label for {entity}')
    if type(entity) != str or entity[0] != 'Q':
        warning_text = 'Wrong entity format. We assume it to be label but check the code'
        sentry_sdk.capture_exception(Exception(warning_text))
        logger.exception(warning_text)
        return entity
    global wikidata
    label = ""
    if entity in wikidata['labels']:
        label = wikidata['labels'][entity]
    else:
        labels = get_triples(["find_label"], [(entity, "")])
        try:
            sep = '"'
            if sep in labels[0]:
                label = labels[0].split('"')[1]
            else:
                label = labels[0]
            logger.debug(f'Answer {label}')
        except Exception as e:
            sentry_sdk.capture_exception(e)
            logger.exception(e)
            logger.info(f'Exception in conversation of labels {labels}')
    return label


def wikidata_process_entities(entity_list, mode='author', bookyear=False,
                              return_plain=False):
    '''
    Processes list of entity candidates(entity_list) using wikidata
    Entities are NOT wikidata objects!!!
    Returns a single name of book or author if it exists.
    P106 - instance of
    Q36180 - author
    P31 - instance of
    Q571 - book
    Q7725634, Q1667921 - book serie
    '''
    try:
        all_found_entities = get_wikidata_entities(entity_list)
        logger.debug(f'Calling wikidata_process_entities for {all_found_entities} mode {mode}')
        requested_entities = []  # All found wikidata entities OF REQUESTED TYPE
        entities_num = len(all_found_entities)
        bool_numbers = None
        if mode == 'author':
            if USE_CACHE:
                bool_numbers = [entity in wikidata['author'] for entity in all_found_entities]
            elif not USE_CACHE or bool_numbers is None:
                parser_info = ["check_triplet" for _ in all_found_entities]
                queries = [(entity, "P106", "Q36180") for entity in all_found_entities]
                bool_numbers = get_triples(parser_info, queries)
            if len(bool_numbers) == len(all_found_entities):
                for entity, bool_number in zip(all_found_entities, bool_numbers):
                    if bool_number:
                        logger.debug('It is author')
                        requested_entities.append(entity)
        elif mode == 'book':
            if USE_CACHE:
                bool_numbers = [entity in wikidata['book'] for entity in all_found_entities]
                for entity, bool_number in zip(all_found_entities, bool_numbers):
                    if bool_number:
                        logger.debug('It is book')
                        requested_entities.append(entity)
                    else:
                        logger.debug('Neither book, nor book serie')
            elif not USE_CACHE or bool_numbers is None:
                parser_info = ["check_triplet" for i in range(3 * entities_num)]
                queries = [(entity, "P31", "Q571") for entity in all_found_entities] + \
                          [(entity, "P31", "Q7725634") for entity in all_found_entities] + \
                          [(entity, "P31", "Q1667921") for entity in all_found_entities]
                bool_numbers = get_triples(parser_info, queries)
                if len(bool_numbers) == 3 * entities_num:
                    bool_numbers_books = bool_numbers[:entities_num]
                    bool_numbers_book_series = [num1 or num2 for num1, num2 in
                                                zip(bool_numbers_books[entities_num:2 * entities_num],
                                                    bool_numbers_books[2 * entities_num:3 * entities_num])]

                    for i in range(len(all_found_entities)):
                        entity = all_found_entities[i]
                        bool_number_book = bool_numbers_books[i]
                        bool_number_book_serie = bool_numbers_book_series[i]
                        if bool_number_book:
                            logger.debug('It is book')
                            requested_entities.append(entity)
                        elif bool_number_book_serie:
                            logger.debug('It is book serie')
                            requested_entities.append(entity)
                        else:
                            logger.debug('Neither book, nor book serie')
        else:
            logger.exception(f'Wrong mode: {mode}')
            return None, None
        requested_entities = sorted(requested_entities, key=lambda x: int(x[1:]))  # Sort entities by frequency
        found_entity, plain_entity, n_years_ago = None, None, None
        if len(requested_entities) > 0:
            plain_entity = requested_entities[0]  # Found entity
            found_entity = entity_to_label(plain_entity)
            n_years_ago = None
            logger.info(f'Found entity {plain_entity}')
            if bookyear and mode == 'book':
                logger.debug(f'Getting published year for {plain_entity}')
                publication_year = get_published_year(plain_entity)
                n_years_ago = datetime.now().year - int(publication_year)
                logger.debug(f'Years ago {n_years_ago}')
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
        plain_entity = None
        found_entity = None
        n_years_ago = None
    if return_plain:
        entity = plain_entity
    else:
        entity = found_entity
    logger.debug(f'Answer {entity} {n_years_ago}')
    return entity, n_years_ago


def best_book_by_author(plain_author_name, default_phrase, plain_last_bookname=None, top_n_best_books=1):
    logger.debug(f'Calling best_book_by_author for {plain_author_name} {plain_last_bookname}')
    # best books
    book_list = None
    if plain_author_name in wikidata['books_of_author']:
        book_list = wikidata['books_of_author'][plain_author_name]
    else:
        logger.debug('No books of author found in pickled data')
        book_list = get_triples(["find_object", "find_object"], [(plain_author_name, "P800", "forw"),
                                                                 (plain_author_name, "P50", "backw")])
        book_list = list(itertools.chain.from_iterable(book_list))
        book_list = list(set(book_list))
    try:
        logger.debug('List of returned books')
        logger.debug(book_list)
        if plain_last_bookname is not None:
            book_list = [j for j in book_list if plain_last_bookname not in j]
        book_list = [x[x.find('Q'):] for x in book_list]  # to unify representations
        logger.debug('List of returned books - processed')
        logger.debug(book_list)
        best_bookname = default_phrase  # default value
        if book_list:
            sorted_book_list = sorted(book_list, key=lambda x: int(x[1:]))  # Sort entities by frequency
            logger.debug(sorted_book_list)
            sorted_bookname_list = [entity_to_label(j)
                                    for j in sorted_book_list]
            logger.debug('List of books with known booknames')
            sorted_bookname_list = [j for j in sorted_bookname_list if j is not None]
            logger.debug(sorted_bookname_list)
            if len(sorted_bookname_list) > 0:
                best_bookname = random.choice(sorted_bookname_list[:top_n_best_books])
        logger.debug('Answer {best_bookname}')
        return best_bookname
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(f'Error processing {book_list}')
        return default_phrase


def parse_author_best_book(annotated_phrase, default_phrase):
    global author_names
    logger.debug(f'Calling parse_author_best_book for {annotated_phrase["text"]}')
    annotated_phrase['text'] = annotated_phrase['text'].lower()
    if re.search(r'\bis\b', annotated_phrase['text']):
        annotated_phrase['text'] = annotated_phrase['text'].split(' is ')[1]
    plain_bookname, _ = get_name(annotated_phrase, 'book', return_plain=True)
    if plain_bookname is None:
        author, _ = get_name(annotated_phrase, 'author')
        if author is None:
            logger.debug('Answer not obtained(no bookname no author)')
            return default_phrase
    else:
        logger.info(f'Processing bookname {plain_bookname}')
        plain_author = who_wrote_book(plain_bookname, return_plain=True)
        if plain_author is not None:
            logger.debug(f'author detected: {plain_author} bookname {plain_bookname}')
            answer = best_book_by_author(plain_author_name=plain_author, plain_last_bookname=plain_bookname,
                                         default_phrase=default_phrase)
            logger.debug(f'Answer is {answer}')
            return answer
        else:
            logger.debug('No author found')
            return default_phrase


dontlike_request = re.compile(r"(not like|not want to talk|not want to hear|not concerned about|"
                              r"over the books|no books|stop talking about|no more books|do not read|"
                              r"not want to listen)", re.IGNORECASE)


def dontlike(last_utterance):
    last_uttr_text = last_utterance['text'].lower()
    last_uttr_text = re.sub('wanna', 'want to', last_uttr_text, re.IGNORECASE)
    last_uttr_text = re.sub("don't'", "do not", last_uttr_text, re.IGNORECASE)
    if re.search(dontlike_request, last_uttr_text) or re.search(NOT_LIKE_PATTERN, last_uttr_text):
        return True
    return False


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
