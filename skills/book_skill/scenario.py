import logging
from os import getenv
from string import punctuation
import sentry_sdk
import random
import requests
import json
import os
import zipfile
import _pickle as cPickle

sentry_sdk.init(getenv('SENTRY_DSN'))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

NOT_LIKE_PATTERN = r"(dislike|not like|not love|not prefer|hate|n't like|" \
                   r"not into|not fond|not crazy|not appriciate|n't appriciate|" \
                   r"disintrested|not for you|not for me|not a big fan|loathe|not stand|n't stand|" \
                   r"not much of fan)"
LIKE_PATTERN = r"(like|love|prefer|adore|enjoy|fond of|passionate of|fan of|interested in|" \
               r"into|for you|for me)"
FAVORITE_PATTERN = r"(favorite|loved|beloved|fondling|best|most interesting)"
ENTITY_SERVICE_URL = getenv('COBOT_ENTITY_SERVICE_URL')
QUERY_SERVICE_URL = getenv('COBOT_QUERY_SERVICE_URL')
QA_SERVICE_URL = getenv('COBOT_QA_SERVICE_URL')
API_KEY = getenv('COBOT_API_KEY')
if "author_namesbooks.pkl" not in os.listdir(os.getcwd()):
    with zipfile.ZipFile("../global_data/author_namesbooks.zip", "r") as zip_ref:
        zip_ref.extractall(os.getcwd())
author_names, author_books = cPickle.load(open('author_namesbooks.pkl', 'rb'))


def was_question_about_book(phrase):
    if type(phrase) == list:
        return any([was_question_about_book(j) for j in phrase])
    return '?' and phrase and any([j in phrase for j in ['book', 'read', 'writer', 'bestseller']])


def opinion_request_detected(annotated_utterance):
    y1 = annotated_utterance['annotations']['intent_catcher'].get('opinion_request', {}).get('detected') == 1
    y2 = 'Opinion_RequestIntent' in annotated_utterance['annotations']['cobot_dialogact']['intents']
    return y1 or y2


def information_request_detected(annotated_utterance):
    return 'Information_RequestIntent' in annotated_utterance['annotations']['cobot_dialogact']['intents']


def request_detected(annotated_utterance):
    return information_request_detected(annotated_utterance) or opinion_request_detected(annotated_utterance)


def opinion_expression_detected(annotated_utterance):
    y1 = 'Opinion_ExpressionIntent' in annotated_utterance['annotations']['cobot_dialogact']['intents']
    y2 = 'Information_DeliveryIntent' in annotated_utterance['annotations']['cobot_dialogact']['intents']
    y3 = was_question_about_book(annotated_utterance['text'])
    return y1 or y2 or y3


def about_book(annotated_utterance):
    # logging.info('about book')
    # logging.info(annotated_utterance)
    y1 = "Entertainment_Books" in annotated_utterance['annotations']['cobot_dialogact']['intents']
    y2 = 'Information_RequestIntent' in annotated_utterance['annotations']['cobot_topics']['text']
    # logging.info('ok')
    return y1 or y2


def get_answer(phrase):
    headers = {'Content-Type': 'application/json;charset=utf-8', 'x-api-key': API_KEY}
    answer = requests.request(url=QA_SERVICE_URL, headers=headers, timeout=2,
                              data=json.dumps({'question': phrase}), method='POST').json()
    return answer['response']


def fan_parse(phrase):
    patterns = ['ever read', 'read', 'ever heard of', 'heard', 'been into', 'interested in',
                'do you like', 'do you enjoy', 'do you prefer', 'a fan of', 'are you familiar with',
                'do you subscribe to', 'the story of', 'are you aware of']
    spl = False
    for pattern in patterns:
        if pattern in phrase:
            phrase = phrase.split(pattern)[1]
            spl = True
    if 'you' in phrase and 'fan?' in phrase and not spl:
        phrase = phrase.split('you')[1]
        if ' fan?' in phrase:
            phrase = phrase.split('fan?')[0]
    phrase = phrase.replace('?', '')
    if 'book' in phrase:
        phrase = phrase.split('book')[0] + 'book'
    return phrase


def parse_author_best_book(annotated_phrase, default_phrase="Fabulous! And what book did impress you the most?"):
    global author_names
    annotated_phrase['text'] = annotated_phrase['text'].lower()
    if ' is ' in annotated_phrase['text']:
        annotated_phrase['text'] = annotated_phrase['text'].split(' is ')[1]
    last_bookname = get_name(annotated_phrase, 'book')
    if last_bookname is None:
        '''
        Look by author name
        '''
        return default_phrase
    else:
        last_bookname = last_bookname.lower()
    try:
        last_bookname = last_bookname.lower()
        '''
        Get author or this book using QUERY LANGUAGE !!!! Not get_answer
        '''
        headers = {'Content-Type': 'application/json;charset=utf-8', 'x-api-key': API_KEY}
        aie_book = get_name(last_bookname, mode='book', return_plain=True)
        answer = requests.request(url=QUERY_SERVICE_URL, headers=headers, timeout=2,
                                  data=json.dumps(
                                      {'query': {'text': 'query d|d' + ' <aio:isTheAuthorOf> ' + aie_book}}),
                                  method='POST').json()
        authorname_plain = '<' + answer['results'][0]['bindingList'][0]['value'] + '>'
        if authorname_plain in author_names:
            author = author_names[authorname_plain]
        else:
            answer = requests.request(
                url=QUERY_SERVICE_URL, headers=headers, data=json.dumps(
                    {'query': {'text': 'query label|' + authorname_plain + ' <aio:prefLabel> ' + 'label'}}),
                method='POST', timeout=2).json()
            author = answer['results'][0]['bindingList'][0]['value']
    except BaseException:
        return default_phrase
    return best_book_by_author(author, last_bookname, default_phrase=default_phrase)
    # Receiving info about the last book ever read, we process info about author


def best_book_by_author(author, last_bookname=None,
                        default_phrase="Fabulous! And what book did impress you the most?"):
    global author_books
    try:
        if author in author_books:
            answer1 = author_books[author]
        else:
            answer1 = get_answer('books of ' + author)
        book_list = answer1.split('include: ')[1].split(',')
        book_list[-1] = book_list[-1][5:-1]
        book_list = [j for j in book_list if all([ban_sign not in j for ban_sign in '[]()'])]
        random.shuffle(book_list)
        if last_bookname is None:
            return book_list[0]
        for book in book_list:
            if book not in last_bookname and last_bookname not in book:
                return book
    except BaseException:
        return default_phrase


def get_name(annotated_phrase, mode='author', return_plain=False):
    if type(annotated_phrase) == str:
        annotated_phrase = {'text': annotated_phrase}
    if mode == 'author':
        class_constraints = [{'dataType': 'aio:Entity', 'value': 'aio:Poet'},
                             {'dataType': 'aio:Entity', 'value': 'aio:BookAuthor'}]
    elif mode == 'book':
        class_constraints = [{'dataType': 'aio:Entity', 'value': 'aio:Book'}]
    else:
        raise Exception('Wrong mode')
    headers = {'Content-Type': 'application/json;charset=utf-8', 'x-api-key': API_KEY}
    named_entities = [annotated_phrase['text']]
    if 'annotations' in annotated_phrase:
        for tmp in annotated_phrase['annotations']['ner']:
            if len(tmp) > 0 and 'text' in tmp[0] and tmp[0]['text'] not in named_entities:
                named_entities.append(tmp[0]['text'])
        for nounphrase in annotated_phrase['annotations']['cobot_nounphrases']:
            if nounphrase not in named_entities:
                named_entities.append(nounphrase)
    entityname = None
    for entity in named_entities:
        if entityname is None:
            try:
                answer = requests.request(url=ENTITY_SERVICE_URL, headers=headers,
                                          data=json.dumps({'mention': {'text': entity},
                                                           'classConstraints': class_constraints}),
                                          method='POST', timeout=2).json()
                entityname_plain = answer['resolvedEntities'][0]['value']
                entityname_plain = '<' + entityname_plain + '>'
                if return_plain:
                    entityname = entityname_plain
                else:
                    entityname = entity
            except BaseException:
                pass
    return entityname


def asking_about_book(annotated_user_phrase):
    user_phrase = annotated_user_phrase['text'].lower()
    cond1 = (all([j in user_phrase for j in ['have', 'you', 'read']]) or 'you think about' in user_phrase)
    if cond1:
        bookname = get_name(annotated_user_phrase, 'book')
        if bookname is not None:
            return True
    return False


def is_stop(annotated_phrase):
    y0 = annotated_phrase['annotations']['intent_catcher'].get('exit', {}).get('detected') == 1
    try:
        y1 = 'Topic_SwitchIntent' in annotated_phrase['annotations']['cobot_dialogact']['intents']
    except BaseException:
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
                      'science tehnology': 'technology books',
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


def fact_about_book(annotated_user_phrase):
    '''
    Edit getting bookname
    '''
    logging.info('fact about')
    logging.info(annotated_user_phrase)
    try:
        bookname = get_name(annotated_user_phrase, 'book')
        reply = get_answer('fact about ' + bookname)
        return reply
    except BaseException:
        return None


def is_previous_was_about_book(dialog):
    return dialog["utterances"][-2]["active_skill"] == 'book_skill'


pphrase1 = ["i'm currently reading sapiens have you heard of that",
            "that's sweet thank you can you tell me about the book sapiens",
            "i don't really read a handmaid's tale have you read sapiens"]

GENRE_PHRASES = json.load(open('genre_phrases.json', 'r'))[0]


class BookSkillScenario:

    def __init__(self):
        self.default_conf = 0.98
        self.default_reply = "I don't know what to answer"
        self.genre_prob = 0.5
        self.bookread_dir = 'bookreads_data.json'
        self.bookreads_data = json.load(open(self.bookread_dir, 'r'))[0]

    def __call__(self, dialogs):
        texts = []
        confidences = []
        # GRAMMARLY!!!!!!
        START_PHRASE = "OK, let's talk about books. Do you love reading?"
        NO_PHRASE_1 = "Why don't you love reading?"
        NO_PHRASE_2 = "I imagine that's good for you."
        # NO_PHRASE_3 = 'I agree. But there are some better books.'
        NO_PHRASE_4 = "OK, I got it. I suppose you know about it everything you need."
        YES_PHRASE_1 = "That's great. What is the last book you have read?"
        YES_PHRASE_2_NO = "That's OK. I can't name it either."
        YES_PHRASE_2 = "Fabulous! And what book did impress you the most?"
        YES_PHRASE_3_1 = "I've also read it. It's an amazing book!"
        YES_PHRASE_3_FACT = "I've read it. It's an amazing book! Would you like to know some facts about it?"
        FAVOURITE_GENRE_ANSWERS = list(GENRE_PHRASES.values())
        FAVOURITE_BOOK_ANSWERS = ['My favourite book is "The Old Man and the Sea" by Ernest Hemingway.']
        GENRE_PHRASE_1 = 'What is your favorite book genre?'

        def GENRE_PHRASE_2(book):
            phrase1 = 'Amazing! Have you read ' + book + ' ? And if you have read it, what do you think about it?'
            return phrase1

        GENRE_PHRASE_ADVICE = "You can read it. You won't regret it!"
        GENRE_LOVE_PHRASE = "I see you love it. It is so wonderful that you read the books you love."
        GENRE_HATE_PHRASE_PART1 = "I see that this book didn't excite you.'"
        GENRE_HATE_PHRASE_PART2 = " It's OK. Maybe some other books will fit you better."
        GENRE_HATE_PHRASE = GENRE_HATE_PHRASE_PART1 + GENRE_HATE_PHRASE_PART2
        GENRE_NOTSURE_PHRASE = "Did you enjoy this book?"
        reply = ""
        confidence = 0
        for dialog in dialogs:
            try:
                # TODO check correct order of concatenation of replies
                text_utterances = [j['text'] for j in dialog['utterances']]
                # logging.info('***'.join([j for j in text_utterances]))
                bot_phrases = [j for i, j in enumerate(text_utterances) if i % 2 == 1]
                if len(bot_phrases) == 0:
                    bot_phrases.append('')
                annotated_user_phrase = dialog['utterances'][-1]
                if len(dialog['utterances']) >= 3:
                    annotated_prev_phrase = dialog['utterances'][-3]
                else:
                    annotated_prev_phrase = None
                # logging.info(str(annotated_user_phrase))
                # logging.info(bot_phrases[-1])
                '''
                Remove punctuation
                '''
                # I don't denote annotated_user_phrase['text'].lower() as a single variable
                # in order not to confuse it with annotated_user_phrase
                if any([j in annotated_user_phrase['text'].lower() for j in ['talk about books', 'chat about books']]):
                    reply, confidence = START_PHRASE, 1
                elif fact_request_detected(annotated_user_phrase):
                    reply, confidence = YES_PHRASE_3_FACT, self.default_conf
                elif genre_request_detected(annotated_user_phrase):
                    reply, confidence = random.choice(FAVOURITE_GENRE_ANSWERS), self.default_conf
                elif book_request_detected(annotated_user_phrase):
                    reply, confidence = random.choice(FAVOURITE_BOOK_ANSWERS), self.default_conf
                elif (YES_PHRASE_3_FACT.lower() == bot_phrases[-1].lower()):
                    if is_no(annotated_user_phrase):
                        reply, confidence = NO_PHRASE_4, self.default_conf
                    else:
                        '''
                        DEFINE PREV PHRASE
                        '''
                        # logging.info('a')
                        for phrase in [annotated_user_phrase, annotated_prev_phrase]:
                            # logging.info(str(phrase))
                            reply, confidence = fact_about_book(phrase), self.default_conf
                            if reply is not None:
                                break
                        if reply is None:
                            reply = self.default_reply
                elif START_PHRASE in bot_phrases:
                    if repeat(annotated_user_phrase):
                        reply, confidence = bot_phrases[-1], self.default_conf
                    elif is_stop(annotated_user_phrase) or side_intent(annotated_user_phrase):
                        reply, confidence = self.default_reply, 0
                    elif START_PHRASE == bot_phrases[-1]:
                        if is_no(annotated_user_phrase):
                            reply, confidence = NO_PHRASE_1, self.default_conf
                            if is_previous_was_about_book(dialog):
                                confidence = 1.0
                        elif is_yes(annotated_user_phrase):
                            reply, confidence = YES_PHRASE_1, self.default_conf
                            if is_previous_was_about_book(dialog):
                                confidence = 1.0
                        else:
                            reply, confidence = self.default_reply, 0
                    elif NO_PHRASE_1 == bot_phrases[-1]:
                        reply, confidence = NO_PHRASE_2, self.default_conf
                    elif YES_PHRASE_1 == bot_phrases[-1]:
                        if is_no(annotated_user_phrase):
                            reply, confidence = YES_PHRASE_2_NO, self.default_conf
                            if is_previous_was_about_book(dialog):
                                confidence = 1.0
                        else:
                            book = parse_author_best_book(annotated_user_phrase, default_phrase=YES_PHRASE_2)
                            reply = 'Interesting. Have you read ' + book + '?'
                            confidence = 0.9
                    elif YES_PHRASE_2 == bot_phrases[-1] or 'Interesting. Have you read ' in bot_phrases[-1]:
                        if is_no(annotated_user_phrase):
                            reply, confidence = NO_PHRASE_2, self.default_conf
                            if is_previous_was_about_book(dialog):
                                confidence = 1.0
                        else:
                            reply, confidence = YES_PHRASE_3_1, self.default_conf
                    elif fact_request_detected(annotated_user_phrase):
                        reply, confidence = fact_about_book(annotated_user_phrase), self.default_conf
                    else:
                        assert reply in [self.default_reply, ""]
                    if reply in [self.default_reply, ""]:
                        if GENRE_PHRASE_1 not in bot_phrases:
                            reply, confidence = GENRE_PHRASE_1, self.default_conf
                        elif GENRE_PHRASE_1 == bot_phrases[-1]:
                            book = get_genre_book(annotated_user_phrase)
                            if book is None:
                                reply, confidence = self.default_reply, 0
                            else:
                                reply, confidence = GENRE_PHRASE_2(book), self.default_conf
                        elif 'Amazing! Have you read ' in bot_phrases[-1]:
                            if tell_me_more(annotated_user_phrase):
                                reply = None
                                bookname = bot_phrases[-1].split('you read ')[1].split('?')[0].strip()
                                for genre in self.bookreads_data:
                                    if self.bookreads_data[genre]['title'] == bookname:
                                        reply, confidence = self.bookreads_data[genre]['description'], self.default_conf
                                if reply is None:
                                    part1 = 'From bot phrase ' + bot_phrases[-1]
                                    part2 = ' bookname *' + bookname + '* didnt match'
                                    raise Exception(part1 + part2)
                            elif is_no(annotated_user_phrase):
                                reply, confidence = GENRE_PHRASE_ADVICE, self.default_conf
                                if is_previous_was_about_book(dialog):
                                    confidence = 1.0
                            elif is_yes(annotated_user_phrase):
                                if is_positive(annotated_user_phrase):
                                    reply, confidence = GENRE_LOVE_PHRASE, self.default_conf
                                elif is_negative(annotated_user_phrase):
                                    reply, confidence = GENRE_HATE_PHRASE, self.default_conf
                                else:
                                    reply, confidence = GENRE_NOTSURE_PHRASE, self.default_conf
                                if is_previous_was_about_book(dialog):
                                    confidence = 1.0

                            else:
                                reply, confidence = self.default_reply, 0
                        elif bot_phrases[-1] == GENRE_NOTSURE_PHRASE:
                            if is_yes(annotated_user_phrase):
                                reply, confidence = GENRE_LOVE_PHRASE, self.default_conf
                                if is_previous_was_about_book(dialog):
                                    confidence = 1.0
                            elif is_no(annotated_user_phrase):
                                reply, confidence = GENRE_HATE_PHRASE, self.default_conf
                                if is_previous_was_about_book(dialog):
                                    confidence = 1.0
                            else:
                                reply, confidence = self.default_reply, 0
                else:
                    author_name = get_name(annotated_user_phrase, 'author')
                    bookname = get_name(annotated_user_phrase, 'book')
                    genre_name = get_genre(annotated_user_phrase['text'], return_name=True)
                    if author_name is not None:
                        reply1 = ' I enjoy reading books of ' + author_name + ' . '
                        best_book = best_book_by_author(author_name, default_phrase=None)
                        if best_book is not None:
                            reply2 = ' My favourite book of this author is ' + best_book
                        else:
                            reply2 = ''
                        reply, confidence = reply1 + reply2, self.default_conf
                    elif bookname is not None:
                        reply, confidence = bookname + ' is an amazing book!', self.default_conf
                    elif genre_name is not None:
                        reply, confidence = GENRE_PHRASES[genre_name], self.default_conf
                    else:
                        reply, confidence = self.default_reply, 0
                if reply in bot_phrases[:-2]:
                    confidence = confidence * 0.5
                assert reply is not None
            except Exception as e:
                logger.exception("exception in book skill")
                sentry_sdk.capture_exception(e)
                reply = "sorry"
                confidence = 0
            texts.append(reply)
            confidences.append(confidence)

        return texts, confidences  # , human_attributes, bot_attributes, attributes
