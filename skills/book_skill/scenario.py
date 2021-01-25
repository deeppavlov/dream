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
from string import punctuation

from common.books import BOOK_SKILL_CHECK_PHRASES, skill_trigger_phrases
from common.tutor import get_tutor_phrase
from common.universal_templates import BOOK_CHANGE_PHRASE, is_switch_topic
from common.utils import get_topics, get_intents

sentry_sdk.init(getenv('SENTRY_DSN'))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)

NOT_LIKE_PATTERN = r"(dislike|not like|not love|not prefer|hate|n't like|" \
                   r"not into|not fond|not crazy|not appriciate|n't appriciate|" \
                   r"disintrested|not for you|not for me|not a big fan|loathe|not stand|n't stand|" \
                   r"not much of fan)"
LIKE_PATTERN = r"(like|love|prefer|adore|enjoy|fond of|passionate of|fan of|interested in|" \
               r"into|for you|for me)"
FAVORITE_PATTERN = r"(favorite|loved|beloved|fondling|best|most interesting)"
GENRE_PHRASES = json.load(open('genre_phrases.json', 'r'))[0]
ENTITY_SERVICE_URL = getenv('COBOT_ENTITY_SERVICE_URL')
QUERY_SERVICE_URL = getenv('COBOT_QUERY_SERVICE_URL')
QA_SERVICE_URL = getenv('COBOT_QA_SERVICE_URL')
# ENTITY_SERVICE_URL = 'https://746y2ig586.execute-api.us-east-1.amazonaws.com/prod//knowledge/v1/entityResolution'
# QUERY_SERVICE_URL = 'https://ssy3pe4ema.execute-api.us-east-1.amazonaws.com/prod/knowledge/v1/query'
#  API_KEY = 'MYF6T5vloa7UIfT1LwftY3I33JmzlTaA86lwlVGm'
API_KEY = getenv('COBOT_API_KEY')
kbqa_files = ['inverted_index_eng.pickle',
              'entities_list.pickle',
              'wiki_eng_q_to_name.pickle',
              'who_entities.pickle']
if "author_namesbooks.pkl" not in os.listdir(os.getcwd()):
    with zipfile.ZipFile("../global_data/author_namesbooks.zip", "r") as zip_ref:
        zip_ref.extractall(os.getcwd())
author_names, author_books = cPickle.load(open('author_namesbooks.pkl', 'rb'))

# if any([kbqa_file not in os.listdir(os.getcwd()) for kbqa_file in kbqa_files]):
#    with tarfile.open('../global_data/wikidata_eng/wiki_eng_files.tar.gz', "r:gz") as tar_ref:
#        tar_ref.extractall(os.getcwd())
# logger.info('Creating linker')
# linker = entity_linking.KBEntityLinker(load_path=os.getcwd(), save_path=os.getcwd(),
#                                       inverted_index_filename="inverted_index_eng.pickle",
#                                       entities_list_filename="entities_list.pickle",
#                                       q2name_filename="wiki_eng_q_to_name.pickle",
#                                       who_entities_filename="who_entities.pickle")
USE_CACHE = True
logger.info('Loading cached wikidata file')
wikidata = cPickle.load(open('wikidata_data.pkl', 'rb'))
logger.info('All files successfully created')


def was_question_about_book(phrase):
    if type(phrase) == list:
        return any([was_question_about_book(j) for j in phrase])
    return '?' and phrase and any([j in phrase for j in ['book', 'read', 'writer', 'bestseller']])


def opinion_request_detected(annotated_utterance):
    y1 = annotated_utterance['annotations']['intent_catcher'].get('opinion_request', {}).get('detected') == 1
    y2 = 'Opinion_RequestIntent' in get_intents(annotated_utterance, which="cobot_dialogact_intents")
    return y1 or y2


def information_request_detected(annotated_utterance):
    return 'Information_RequestIntent' in get_intents(annotated_utterance, which="cobot_dialogact_intents")


def request_detected(annotated_utterance):
    return information_request_detected(annotated_utterance) or opinion_request_detected(annotated_utterance)


def opinion_expression_detected(annotated_utterance):
    _intents = get_intents(annotated_utterance, which="cobot_dialogact_intents")
    y1 = 'Opinion_ExpressionIntent' in _intents
    y2 = 'Information_DeliveryIntent' in _intents
    y3 = was_question_about_book(annotated_utterance['text'])
    return y1 or y2 or y3


def about_book(annotated_utterance):
    # logger.debug('aboutg book')
    # logger.debug(annotated_utterance)
    y1 = "Entertainment_Books" in get_topics(annotated_utterance, which="cobot_dialogact_topics")
    y2 = 'Information_RequestIntent' in get_topics(annotated_utterance, which='cobot_topics')
    # logger.debug('ok')
    return y1 or y2


def asking_about_book(annotated_user_phrase):
    user_phrase = annotated_user_phrase['text'].lower()
    cond1 = (all([j in user_phrase for j in ['have', 'you', 'read']]) or 'you think about' in user_phrase)
    if cond1:
        bookname, _ = get_name(annotated_user_phrase, 'book')
        if bookname is not None:
            return True
    return False


def is_stop(annotated_phrase):
    y0 = annotated_phrase['annotations']['intent_catcher'].get('exit', {}).get('detected') == 1
    try:
        y1 = 'Topic_SwitchIntent' in get_intents(annotated_phrase, which="cobot_dialogact_intents")
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(f'Bug in get_intents {annotated_phrase}')
        y1 = False
    user_phrase = annotated_phrase['text']
    user_phrase = user_phrase.lower()
    user_phrase = user_phrase.replace("n't", "not")
    y2 = ('stop' in user_phrase or 'not' in user_phrase or 'about something else' in user_phrase)
    if y0 or y1 or y2:
        return True
    else:
        return False


def is_yes(annotated_phrase):
    y1 = annotated_phrase['annotations']['intent_catcher'].get('yes', {}).get('detected') == 1
    user_phrase = annotated_phrase['text']
    for sign in punctuation:
        user_phrase = user_phrase.replace(sign, ' ')
    y2 = ' yes ' in user_phrase
    return y1 or y2


def is_no(annotated_phrase):
    y1 = annotated_phrase['annotations']['intent_catcher'].get('no', {}).get('detected') == 1
    user_phrase = annotated_phrase['text']
    user_phrase = user_phrase.replace("n't", ' not ')
    for sign in punctuation:
        user_phrase = user_phrase.replace(sign, ' ')
    y2 = ' no ' in user_phrase or ' not ' in user_phrase
    return y1 or y2


def repeat(annotated_phrase):
    return annotated_phrase['annotations']['intent_catcher'].get('repeat', {}).get('detected') == 1


def side_intent(annotated_phrase):
    side_intent_list = ["don't understand", 'what_can_you_do', 'what_is_your_job', 'what_is_your_name',
                        'what_time', 'where_are_you_from', 'who_made_you']
    for side_intent in side_intent_list:
        if annotated_phrase['annotations']['intent_catcher'].get(side_intent, {}).get('detected') == 1:
            return True
        return False


def is_negative(annotated_phrase):
    sentiment = annotated_phrase['annotations']['sentiment_classification']['text'][0]
    return sentiment in ["negative", "very_negative"]


def is_positive(annotated_phrase):
    sentiment = annotated_phrase['annotations']['sentiment_classification']['text'][0]
    return sentiment in ["positive", "very_positive"]


def tell_me_more(annotated_phrase):
    cond1 = annotated_phrase['annotations']['intent_catcher'].get('tell_me_more', {}).get('detected') == 1
    cond2 = 'tell me ' in annotated_phrase['text'] and ([j in annotated_phrase['text'] for j in ['about', 'of']])
    return cond1 or cond2


def fact_request_detected(annotated_user_phrase):
    cond1 = 'have you read ' in annotated_user_phrase['text'].lower()
    cond2 = opinion_request_detected(annotated_user_phrase) and about_book(annotated_user_phrase)
    cond3 = asking_about_book(annotated_user_phrase)
    # removed cond4 due to the bug in information_request_detected
    # cond4 = information_request_detected(annotated_user_phrase)
    return cond1 or cond2 or cond3  # or cond4


def get_genre_book(annotated_user_phrase, bookreads='bookreads_data.json'):
    '''
    TODO: Parse genre from phrase and get a book of this genre
    '''
    logger.debug('genre book about')
    logger.debug(annotated_user_phrase)
    bookreads_data = json.load(open(bookreads, 'r'))[0]
    user_phrase = annotated_user_phrase['text']
    genre = get_genre(user_phrase)
    if genre is None:
        genre = 'fiction'
    book = bookreads_data[genre]['title']
    return book


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


def genre_request_detected(annotated_user_phrase):
    phrase = annotated_user_phrase['text'].lower()
    phrase = phrase.replace('favourite', 'favorite')
    return 'your favorite' in phrase and 'genre' in phrase


def book_request_detected(annotated_user_phrase):
    phrase = annotated_user_phrase['text'].lower()
    phrase = phrase.replace('favourite', 'favorite')
    return 'your favorite' in phrase and 'book' in phrase


def get_answer(phrase):
    logger.debug('Getting COBOT anwer for phrase')
    logger.debug(phrase)
    headers = {'Content-Type': 'application/json;charset=utf-8', 'x-api-key': API_KEY}
    answer = requests.request(url=QA_SERVICE_URL, headers=headers, timeout=2,
                              data=json.dumps({'question': phrase}), method='POST').json()
    try:
        return_value = answer['response']
        logger.debug(answer['response'])
        logger.debug(f'Response obtained: {return_value}')
        return return_value
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
        logger.debug('Response not obtained')
        return None


def fact_about_book(annotated_user_phrase):
    logger.debug('fact about')
    logger.debug(annotated_user_phrase)
    bookname, _ = get_name(annotated_user_phrase, 'book')
    logger.debug('Getting a fact about bookname')
    reply = get_answer(f'fact about {bookname}')
    return reply


def get_triples(parser_info, queries):
    WIKIDATA_URL = os.getenv("WIKIDATA_URL")
    logger.debug(f"Calling get_triples, parser_info {parser_info}, queries {queries}")
    t = time.time()
    response = [[]]
    resp = requests.post(WIKIDATA_URL,
                         json={"query": queries, "parser_info": parser_info},
                         timeout=1)
    if resp.status_code == 200:
        response = [elem[0] for elem in resp.json()]
    else:
        logger.debug("Could not access wiki parser")
    exec_time = round(time.time() - t, 2)
    logger.debug(f'Response obtained with exec time {exec_time}')

    return response


def request_entities(entity):
    logger.debug(f'Calling request_entities for {entity}')
    ENTITY_LINKING_URL = os.getenv("ENTITY_LINKING_URL")
    assert type(entity) == str
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
    assert len(entities) == len(probs)
    return entities, probs


def is_previous_was_about_book(dialog):
    return len(dialog['utterances']) >= 2 and dialog["utterances"][-2]["active_skill"] == 'book_skill'


def get_entities(annotated_phrase):
    named_entities = [annotated_phrase['text']]
    if 'annotations' in annotated_phrase:
        for tmp in annotated_phrase['annotations']['ner']:
            if len(tmp) > 0 and 'text' in tmp[0] and tmp[0]['text'] not in named_entities:
                named_entities.append(tmp[0]['text'])
        for nounphrase in annotated_phrase['annotations'].get("cobot_nounphrases", []):
            if nounphrase not in named_entities:
                named_entities.append(nounphrase)
    return named_entities


def preprocess_entities(named_entities):
    logger.debug(f'Calling preprocess_entities for {str(named_entities)}')
    # auhillary function from get_name aimed at enitites processing
    processed_entities = []
    banned_entities = ['tik tok', 'minecraft', 'the days']
    for entity in named_entities:
        if 'when' in entity and 'was first published' in entity:
            try:
                entity = entity.split('when')[1].split('was first published')[0]
            except Exception as e:
                sentry_sdk.capture_exception(e)
                logger.exception(f'Strange entity {entity}')
        for pattern in ['read was', 'book is', 'book was']:
            if pattern in entity:
                entity = entity.split(pattern)[1]
        if entity not in banned_entities:
            processed_entities.append(entity)
    return processed_entities


def get_name(annotated_phrase, mode='author', bookyear=True, return_plain=False):
    # Annotated phrase: str or dict
    # Getting author name or book name
    # Returning entity name and(on request) when the book was published
    logger.debug('Calling get_name for')

    if type(annotated_phrase) == str:
        annotated_phrase = {'text': annotated_phrase}
    logger.debug(annotated_phrase['text'])
    logger.debug(f'Mode {mode}')
    if return_plain:
        logger.debug("With plain")
    named_entities = get_entities(annotated_phrase)
    processed_entities = preprocess_entities(named_entities)
    logger.debug('named entities')
    logger.debug(named_entities)
    logger.debug('processed entities')
    logger.debug(processed_entities)

    entityname, n_years = wikidata_process_entities(processed_entities, mode=mode, bookyear=bookyear,
                                                    return_plain=return_plain)
    logger.debug(f'Answer {str(entityname)} {str(n_years)}')
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
    assert type(book_entity) == str and book_entity[0] == 'Q'
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
    assert type(entity) == str and entity[0] == 'Q'
    global wikidata
    label = ""
    if entity in wikidata['labels']:
        label = wikidata['labels'][entity]
    else:
        labels = get_triples(["find_label"], [(entity, "")])[0]
        try:
            sep = '"'
            if sep in labels[0]:
                label = labels[0].split('"')[1]
            else:
                label = labels[0]
            logger.debug(f'Answer {label}')
        except Exception as e:
            sentry_sdk.capture_exception(e)
            logger.exception(f'Exception in converstion of labels {labels}')
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
    found_entity, n_years_ago = None, None
    if len(requested_entities) > 0:
        found_entity = requested_entities[0]  # Found entity
        n_years_ago = None
        logger.info(f'Found entity {found_entity}')
        if bookyear and mode == 'book':
            logger.debug('Getting published year for ' + str(found_entity))
            publication_year = get_published_year(found_entity)
            n_years_ago = datetime.now().year - int(publication_year)
            logger.debug('Years ago ' + str(n_years_ago))
        if not return_plain:
            found_entity = entity_to_label(found_entity)
    logger.debug('Answer ' + str(found_entity) + ' ' + str(n_years_ago))
    return found_entity, n_years_ago


def best_book_by_author(plain_author_name, plain_last_bookname=None,
                        top_n_best_books=1,
                        default_phrase="Fabulous! And what book did impress you the most?"):
    logger.debug('Calling best_book_by_author for ' + str(plain_author_name) + ' ' + str(plain_last_bookname))
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


def parse_author_best_book(annotated_phrase, default_phrase="Fabulous! And what book did impress you the most?"):
    global author_names
    assert type(annotated_phrase['text']) == str
    logger.debug('Calling parse_author_best_book for ')
    logger.debug(annotated_phrase['text'])
    annotated_phrase['text'] = annotated_phrase['text'].lower()
    if ' is ' in annotated_phrase['text']:
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
            logger.debug('author detected')
            logger.debug(plain_author)
            logger.debug(f'bookname {plain_bookname}')
            answer = best_book_by_author(plain_author_name=plain_author, plain_last_bookname=plain_bookname,
                                         default_phrase=default_phrase)
            logger.debug(f'Answer is {answer}')
            return answer
        else:
            logger.debug('No author found')
            return default_phrase


dontlike_request = re.compile(r"(not like|not want to talk|not want to hear|not concerned about|"
                              r"over the books|no books|stop talking about|no more books|"
                              r"not want to listen)", re.IGNORECASE)


def dontlike(last_utterance):
    last_uttr_text = last_utterance['text'].lower()
    last_uttr_text = re.sub('wanna', 'want to', last_uttr_text, re.IGNORECASE)
    last_uttr_text = re.sub("don't'", "do not", last_uttr_text, re.IGNORECASE)
    if re.search(dontlike_request, last_uttr_text):
        return True
    return False


class BookSkillScenario:

    def __init__(self):
        self.default_conf = 1  # to be rarer interrupted by cobotqa
        self.default_reply = "I don't know what to answer"
        self.genre_prob = 1
        self.bookread_dir = 'bookreads_data.json'
        self.bookreads_data = json.load(open(self.bookread_dir, 'r'))[0]

    def __call__(self, dialogs):
        texts, confidences = [], []
        human_attrs, bot_attrs, attrs = [], [], []
        # GRAMMARLY!!!!!!
        START_PHRASE = "OK, let's talk about books. Do you love reading?"
        NO_PHRASE_1 = "Why don't you love reading?"
        NO_PHRASE_2 = BOOK_CHANGE_PHRASE
        # NO_PHRASE_3 = 'I agree. But there are some better books.'
        NO_PHRASE_4 = BOOK_CHANGE_PHRASE
        YES_PHRASE_1 = "That's great. What is the last book you have read?"
        YES_PHRASE_2_NO = "That's OK. I can't name it either."
        YES_PHRASE_2 = "Fabulous! And what book did impress you the most?"
        YES_PHRASE_3_1 = "I've also read it. It's an amazing book! Do you know when it was first published?"
        YES_PHRASE_3_FACT = "I've read it. It's an amazing book! Would you like to know some facts about it?"
        YES_PHRASE_4 = " I didn't exist in that time. " + get_tutor_phrase()
        FAVOURITE_GENRE_ANSWERS = list(GENRE_PHRASES.values())
        FAVOURITE_BOOK_ANSWERS = ['My favourite book is "The Old Man and the Sea" by Ernest Hemingway.',
                                  'The Old Man and the Sea tells the story of a battle between a fisherman '
                                  'and a large marlin. This is my favourite story, it is truly fascinating.']
        GENRE_PHRASE_1 = 'What is your favorite book genre?'

        def GENRE_PHRASE_2(book):
            phrase1 = f'Amazing! Have you read {book} ? And if you have read it, what do you think about it?'
            return phrase1

        GENRE_PHRASE_ADVICE = "You can read it. You won't regret it!"
        GENRE_LOVE_PHRASE = "I see you love it. It is so wonderful that you read the books you love."
        GENRE_HATE_PHRASE_PART1 = "I see that this book didn't excite you.'"
        GENRE_HATE_PHRASE_PART2 = " It's OK. Maybe some other books will fit you better."
        GENRE_HATE_PHRASE = GENRE_HATE_PHRASE_PART1 + GENRE_HATE_PHRASE_PART2
        GENRE_NOTSURE_PHRASE = "Did you enjoy this book?"
        UNKNOWNBOOK_QUESTIONS = ["Sorry I've never heard about this book. What is it about?",
                                 "Not sure if I've heard of this book before. What is it about?",
                                 "I suppose I've never heard about this book before. What did you like about it?",
                                 "Oops. I guess I've never heard about this book before. "
                                 "What caught your attention in this book?"]
        reply = ""
        confidence = 0
        default_attr = {}
        for dialog in dialogs:
            try:
                # TODO check correct order of concatenation of replies
                human_attr = dialog["human"]["attributes"]
                if 'book_skill' not in human_attr:
                    human_attr['book_skill'] = dict()
                    if 'used_phrases' not in human_attr['book_skill']:
                        human_attr['book_skill']['used_phrases'] = []
                text_utterances = [j['text'] for j in dialog['utterances']]
                # logger.debug('***'.join([j for j in text_utterances]))
                bot_phrases = [j for i, j in enumerate(text_utterances) if i % 2 == 1]
                if len(bot_phrases) == 0:
                    bot_phrases.append('')
                logger.debug('bot phrases')
                logger.debug(bot_phrases)
                user_phrases = []
                annotated_user_phrase = dialog['utterances'][-1]
                annotated_user_phrase['text'] = annotated_user_phrase['text'].replace('.', '')
                user_phrases.append(annotated_user_phrase['text'])
                if len(dialog['utterances']) >= 3:
                    annotated_prev_phrase = dialog['utterances'][-3]
                    annotated_prev_phrase['text'] = annotated_prev_phrase['text'].replace('.', '')
                    user_phrases.append(annotated_prev_phrase['text'])
                else:
                    annotated_prev_phrase = None
                # logger.debug(str(annotated_user_phrase))
                # logger.debug(bot_phrases[-1])
                logger.debug('User phrase: last and prev from last')
                logger.debug(user_phrases)
                '''
                Remove punctuation
                '''
                used_trigger = any([j in bot_phrases[-1] for j in skill_trigger_phrases()])
                was_checkphrase = [j.lower() in bot_phrases[-1].lower() for j in BOOK_SKILL_CHECK_PHRASES]
                # I don't denote annotated_user_phrase['text'].lower() as a single variable
                # in order not to confuse it with annotated_user_phrase
                cond1 = any([j in annotated_user_phrase['text'].lower()
                             for j in ['talk about books', 'chat about books']])
                if cond1 and not is_no(annotated_user_phrase):
                    logger.debug('Detected talk about books. Calling start phrase')
                    reply, confidence = START_PHRASE, 1
                elif dontlike(annotated_user_phrase):
                    reply, confidence = '', 0
                elif is_switch_topic(annotated_user_phrase):
                    reply, confidence = BOOK_CHANGE_PHRASE, 0.9
                elif (fact_request_detected(annotated_user_phrase)
                      and fact_about_book(annotated_user_phrase) is not None):
                    logger.debug('Detected fact request')
                    reply, confidence = YES_PHRASE_3_FACT, self.default_conf
                elif genre_request_detected(annotated_user_phrase):
                    logger.debug('Detected genre request')
                    reply, confidence = random.choice(FAVOURITE_GENRE_ANSWERS), self.default_conf
                elif book_request_detected(annotated_user_phrase):
                    logging.debug('Detected book request')
                    if FAVOURITE_BOOK_ANSWERS[0] not in human_attr['book_skill']['used_phrases']:
                        reply = FAVOURITE_BOOK_ANSWERS[0]
                    elif FAVOURITE_BOOK_ANSWERS[1] not in human_attr['book_skill']['used_phrases']:
                        reply = FAVOURITE_BOOK_ANSWERS[1]
                    else:
                        reply = random.choice(FAVOURITE_BOOK_ANSWERS)
                    confidence = self.default_conf
                elif (YES_PHRASE_3_FACT.lower() == bot_phrases[-1].lower()):
                    logging.debug('Previous bot phrase was fact request')
                    if is_no(annotated_user_phrase):
                        logging.debug('Detected is_no answer')
                        reply, confidence = NO_PHRASE_4, self.default_conf
                    else:
                        '''
                        DEFINE PREV PHRASE
                        '''
                        # logging.debug('a')
                        for phrase in [annotated_user_phrase, annotated_prev_phrase]:
                            # logging.debug(str(phrase))
                            logging.debug('Finding fact about book')
                            reply, confidence = fact_about_book(phrase), self.default_conf
                            if reply is not None:
                                logging.debug('Found a bookfact')
                                break
                        if reply is None:
                            logging.debug('Fact about book returned None')
                            reply = self.default_reply
                elif 'was first published' in bot_phrases[-1]:
                    logger.debug('We have just asked when the book was published: getting name for')
                    logger.debug(annotated_prev_phrase['text'])
                    bookname, n_years_ago = get_name(annotated_prev_phrase, mode='book', bookyear=True)
                    if bookname is None:
                        logger.debug('No bookname detected')
                        reply, confidence = '', 0
                    else:
                        logger.debug('Bookname detected')
                        if n_years_ago > 0:
                            recency_phrase = f"{n_years_ago} years ago! "
                        else:
                            recency_phrase = 'Just recently! '
                        reply, confidence = recency_phrase + YES_PHRASE_4, self.default_conf
                elif START_PHRASE in human_attr['book_skill']['used_phrases']:
                    logging.debug('We have already said starting phrase')
                    if repeat(annotated_user_phrase):
                        logger.debug('Repeat intent detected')
                        reply, confidence = bot_phrases[-1], self.default_conf
                    elif is_stop(annotated_user_phrase) or side_intent(annotated_user_phrase):
                        logger.debug('Stop/side intent detected')
                        reply, confidence = self.default_reply, 0
                    elif START_PHRASE == bot_phrases[-1]:
                        logger.debug('We have just said starting phrase')
                        if is_no(annotated_user_phrase):
                            logger.debug('Detected answer NO')
                            reply, confidence = NO_PHRASE_1, self.default_conf
                            if is_previous_was_about_book(dialog):
                                confidence = 1.0
                        elif is_yes(annotated_user_phrase):
                            logger.debug('Detected asnswer YES')
                            reply, confidence = YES_PHRASE_1, self.default_conf
                            if is_previous_was_about_book(dialog):
                                confidence = 1.0
                        else:
                            logger.debug('No answer detected. Return nothing.')
                            reply, confidence = self.default_reply, 0
                    elif NO_PHRASE_1 == bot_phrases[-1]:
                        logger.debug('We have just said NO_PHRASE_1')
                        reply, confidence = NO_PHRASE_2, self.default_conf
                    elif YES_PHRASE_1 == bot_phrases[-1]:
                        logger.debug('We have just said YES_PHRASE_1')
                        if is_no(annotated_user_phrase):
                            logger.debug('NO answer detected')
                            reply, confidence = YES_PHRASE_2_NO, self.default_conf
                            if is_previous_was_about_book(dialog):
                                confidence = 1.0
                        else:
                            logger.debug('Does not detect NO. Parsing author best book for')
                            logger.debug(annotated_user_phrase['text'])
                            book = parse_author_best_book(annotated_user_phrase, default_phrase=YES_PHRASE_2)
                            if book != YES_PHRASE_2 and book.lower() not in annotated_user_phrase['text'].lower():
                                logger.debug('Could not find author best book. Returning default answer')
                                reply = f'Interesting. Have you read {book}?'
                                confidence = 0.9
                            else:
                                logger.debug(f"Best book for {annotated_user_phrase['text']} not retrieved")
                                reply, confidence = YES_PHRASE_2, 0.9
                    elif YES_PHRASE_2 == bot_phrases[-1]:
                        logger.debug('We have just said YES_PHRASE_2')
                        if is_no(annotated_user_phrase):
                            logger.debug('NO answer detected')
                            reply, confidence = NO_PHRASE_2, self.default_conf
                            if is_previous_was_about_book(dialog):
                                confidence = 1.0
                        else:
                            '''
                            FIND A BOOK IN ANNOTATED_USER_PPHRASE
                            '''
                            logger.debug('Did not detect NO answer. Getting name for')
                            logger.debug(annotated_user_phrase['text'])
                            bookname, bookyear = get_name(annotated_user_phrase, mode='book', bookyear=True)
                            if bookname is None:
                                logger.debug('No bookname detected: returning default reply')
                                reply, confidence = '', 0
                            else:
                                logger.debug('Bookname detected: returning YES_PHRASE_3_1')
                                reply, confidence = YES_PHRASE_3_1, self.default_conf
                    elif fact_request_detected(annotated_user_phrase):
                        logger.debug('Fact request detected: returning fact about book')
                        logger.debug(annotated_user_phrase['text'])
                        reply, confidence = fact_about_book(annotated_user_phrase), self.default_conf
                    else:
                        logger.debug('Asserting we have returned no reply')
                        assert reply in [self.default_reply, ""]
                    if reply in [self.default_reply, ""]:
                        if GENRE_PHRASE_1 not in human_attr['book_skill']['used_phrases']:
                            logging.debug('GENRE_PHRASE_1 not in bot phrases: returning it')
                            reply, confidence = GENRE_PHRASE_1, self.default_conf
                        elif GENRE_PHRASE_1 == bot_phrases[-1]:
                            logger.debug('Last phrase is GENRE_PHRASE_1 : getting genre book for ')
                            logger.debug(str(annotated_user_phrase['text']))
                            book = get_genre_book(annotated_user_phrase)
                            if book is None or is_no(annotated_user_phrase):
                                logger.debug('No book found')
                                reply, confidence = self.default_reply, 0
                            else:
                                logger.debug(f'Returning genre phrase for {book}')
                                reply, confidence = GENRE_PHRASE_2(book), self.default_conf
                        elif 'Amazing! Have you read ' in bot_phrases[-1]:
                            logger.debug('"Amazing! Have uou read"  in last bot phrase')
                            if tell_me_more(annotated_user_phrase):
                                logger.debug('Tell me more intent detected')
                                reply = None
                                bookname = bot_phrases[-1].split('you read ')[1].split('?')[0].strip()
                                logger.debug(f'Detected name {bookname} in last_bot_phrase')
                                for genre in self.bookreads_data:
                                    if self.bookreads_data[genre]['title'] == bookname:
                                        logger.debug(f'Returning phrase for book of genre {genre}')
                                        reply, confidence = self.bookreads_data[genre]['description'], self.default_conf
                                if reply is None:
                                    part1 = f'From bot phrase {bot_phrases[-1]}'
                                    part2 = f' bookname * bookname * didnt match'
                                    sentry_sdk.capture_exception(Exception(part1 + part2))
                                    logger.exception(part1 + part2)
                            elif is_no(annotated_user_phrase):
                                logger.debug('intent NO detected')
                                reply, confidence = GENRE_PHRASE_ADVICE, self.default_conf
                                if is_previous_was_about_book(dialog):
                                    confidence = 1.0
                            elif is_yes(annotated_user_phrase):
                                logger.debug('YES intent detected')
                                if is_positive(annotated_user_phrase):
                                    logger.debug('positive intent detected')
                                    reply, confidence = GENRE_LOVE_PHRASE, self.default_conf
                                elif is_negative(annotated_user_phrase):
                                    logger.debug('negative intent detected')
                                    reply, confidence = GENRE_HATE_PHRASE, self.default_conf
                                else:
                                    logger.debug('Without detected intent returning GENRE_NOTSURE_PHRASE')
                                    reply, confidence = GENRE_NOTSURE_PHRASE, self.default_conf
                                if is_previous_was_about_book(dialog):
                                    confidence = 1.0

                            else:
                                logger.debug('No intent detected. Returning nothing')
                                reply, confidence = self.default_reply, 0
                        elif bot_phrases[-1] == GENRE_NOTSURE_PHRASE:
                            logger.debug('Last phrase was GENRE_NOTSURE_PHRASE')
                            if is_yes(annotated_user_phrase):
                                logger.debug('YES intent detected')
                                reply, confidence = GENRE_LOVE_PHRASE, self.default_conf
                                if is_previous_was_about_book(dialog):
                                    confidence = 1.0
                            elif is_no(annotated_user_phrase):
                                logger.debug('NO intent detected')
                                reply, confidence = GENRE_HATE_PHRASE, self.default_conf
                                if is_previous_was_about_book(dialog):
                                    confidence = 1.0
                            else:
                                logger.debug('Detected neither YES nor NO intent. Returning nothing')
                                reply, confidence = self.default_reply, 0
                else:
                    logger.debug('Getting whether phrase contains name of author, book or genre')
                    author_name, _ = get_name(annotated_user_phrase, 'author')
                    bookname, n_years_ago = get_name(annotated_user_phrase, 'book', bookyear=True)
                    genre_name = get_genre(annotated_user_phrase['text'], return_name=True)
                    if author_name is not None:
                        logger.debug(f'Phrase contains name of author {author_name}')
                        reply1 = f' I enjoy reading books of {author_name} . '
                        best_book = best_book_by_author(author_name, default_phrase=None)
                        if best_book is not None:
                            reply2 = f' My favourite book of this author is {best_book}'
                        else:
                            reply2 = ''
                        reply, confidence = reply1 + reply2, self.default_conf
                    elif bookname is not None:
                        logger.debug(f'Phrase contains name of book {bookname}')
                        reply = f'{bookname} is an amazing book! '
                        if n_years_ago is not None:
                            reply = f'{reply} Do you know when it was first published?'
                        if was_checkphrase:
                            confidence = 0.99
                        else:
                            confidence = self.default_conf
                    elif genre_name is not None:
                        prev_genre = get_genre(annotated_prev_phrase['text'], return_name=True)
                        only_one_phrase = len(GENRE_PHRASES[genre_name]) == 1
                        logger.debug(f'Phrase contains name of genre {genre_name}')
                        if prev_genre != genre_name or only_one_phrase:
                            reply, confidence = GENRE_PHRASES[genre_name][0], self.default_conf
                        else:
                            reply, confidence = GENRE_PHRASES[genre_name][1], self.default_conf
                    elif was_checkphrase:
                        logger.info('The answer probably was about book, but we cant find this book')
                        reply = random.choice(UNKNOWNBOOK_QUESTIONS)
                        confidence = 0.9
                    elif used_trigger:
                        # phrase only about bookname in the same way as trigger
                        reply, confidence = 'Sorry, I could not find this book. Please, tell me about it', 0.85
                    elif 'I enjoy reading book of ' in bot_phrases[-1]:
                        author_name = bot_phrases[-1].split('enjoy reading book of')[1].split('.')[0]
                        reply, confidence = f'What books of {author_name} do you like?', 0.8
                    else:
                        logger.debug('Final branch. Say starting phrase.')
                        reply, confidence = START_PHRASE, 0.7
                    if not (used_trigger or was_checkphrase):
                        confidence = confidence * 0.5
                if reply in bot_phrases[:-2]:
                    confidence = confidence * 0.5
                assert reply is not None
            except Exception as e:
                logger.exception("exception in book skill")
                sentry_sdk.capture_exception(e)
                reply = ""
                confidence = 0

            if isinstance(reply, list):
                reply = " ".join(reply)
            if not is_previous_was_about_book(dialog) and confidence > 0.95 and reply != START_PHRASE:
                confidence = 0.95
            if reply in human_attr['book_skill']['used_phrases']:
                confidence = 0.5

            texts.append(reply)
            human_attr['book_skill']['used_phrases'].append(reply)
            confidences.append(confidence)
            human_attrs.append(human_attr)
            attrs.append(default_attr)
            bot_attrs.append(default_attr)

        return texts, confidences, human_attrs, bot_attrs, attrs
