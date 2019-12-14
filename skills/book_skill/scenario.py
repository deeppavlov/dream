import logging
from os import getenv
from string import punctuation
import sentry_sdk
import random
import re
import requests
import json

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


# QUERY_SERVICE_URL = 'https://ssy3pe4ema.execute-api.us-east-1.amazonaws.com/prod/knowledge/v1/query'
# ENTITY_SERVICE_URL = 'https://746y2ig586.execute-api.us-east-1.amazonaws.com/prod//knowledge/v1/entityResolution'
# QA_SERVICE_URL = 'https://06421kpunk.execute-api.us-east-1.amazonaws.com/prod/qa/v1/answer'
# API_KEY = 'MYF6T5vloa7UIfT1LwftY3I33JmzlTaA86lwlVGm'


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
    y2 = 'Information_DeliveryIntent' in annotated_utterance['annotations']['cobot_dialog_act']['intents']
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
    answer = requests.request(url=QA_SERVICE_URL, headers=headers,
                              data=json.dumps({'question': phrase}), method='POST').json()
    return answer['response']


def parse_author_best_book(annotated_phrase, default_phrase="Fabulous! And what book did impress you the most?",
                           default_confidence=0.9):
    phrase = annotated_phrase['text'].lower()
    if ' is ' in phrase:
        phrase = phrase.split(' is ')[1]
    best_bookname = get_bookname(phrase)
    if best_bookname is None:
        return default_phrase, default_confidence
    try:
        about_best_book = get_answer(best_bookname)
        author = about_best_book.split('author ')[1]
        match = re.search(r'[a-z][.] [A-Z]', author)
        span = match.span()[0] + 1
        author = author[:span + 1]
        answer1 = get_answer('books of ' + author)
        book_list = answer1.split('include: ')[1].split(',')
    except BaseException:
        return default_phrase, default_confidence
    book_list[-1] = book_list[-1][5:-1]
    random.shuffle(book_list)
    for book in book_list:
        if book not in best_bookname and best_bookname not in book:
            return 'Interesting. Have you read ' + book + ' ?', default_confidence
    return default_phrase, default_confidence
    # Receiving info about the last book ever read, we зкщсуыы штащ фищге фгерщк


def get_bookname(annotated_phrase):
    class_constraints = [{'dataType': 'aio:Entity', 'value': 'aio:Book'}]
    headers = {'Content-Type': 'application/json;charset=utf-8', 'x-api-key': API_KEY}
    try:
        answer = requests.request(url=ENTITY_SERVICE_URL, headers=headers,
                                  data=json.dumps({'mention': {'text': annotated_phrase['text']},
                                                   'classConstraints': class_constraints}), method='POST').json()
    except BaseException:
        return None
    if len(answer['resolvedEntities']) > 0:
        bookname_plain = answer['resolvedEntities'][0]
        try:
            answer = requests.request(url=QUERY_SERVICE_URL, headers=headers,
                                      data=json.dumps(
                                          {'query': {'text': 'query label|' + bookname_plain + ' <aio:prefLabel> label'
                                                     }}), method='POST').json()
            bookname = answer['results']['value']
            return bookname
        except BaseException:
            return None
    return None


def asking_about_book(annotated_user_phrase):
    user_phrase = annotated_user_phrase['text'].lower()
    cond1 = (all([j in user_phrase for j in ['have', 'you', 'read']]) or 'you think about' in user_phrase)
    if cond1:
        bookname = get_bookname(annotated_user_phrase)
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
    return annotated_phrase['annotations']['intent_catcher'].get('tell_me_more', {}).get('detected') == 1


def fact_request_detected(annotated_user_phrase):
    cond1 = 'have you read ' in annotated_user_phrase['text'].lower()
    cond2 = opinion_request_detected(annotated_user_phrase) and about_book(annotated_user_phrase)
    cond3 = asking_about_book(annotated_user_phrase)
    # removed cond3 due to the bug in information_request_detected
    # cond4 = tell_me_more(annotated_user_phrase) or information_request_detected(annotated_user_phrase)
    return cond1 or cond2 or cond3  # or cond4


def get_genre_book(annotated_user_phrase, bookreads='bookreads_data.json'):
    '''
    TODO: Parse genre from phrase and get a book of this genre
    '''
    bookreads_data = json.load(open(bookreads, 'r'))[0]
    user_phrase = annotated_user_phrase['text']
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
    elif any([j in user_phrase for j in ['humor', 'funny', 'laugh']]):
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
    book = bookreads_data[genre]['title']
    return book


class BookSkillScenario:

    def __init__(self):
        self.default_conf = 0.98
        self.default_reply = "I don't know what to answer"
        self.genre_prob = 0.5
        self.bookread_dir = 'bookreads_data.json'

    def fact_about_book(self, annotated_phrase):
        '''
        Edit getting bookname
        '''
        bookname = get_bookname(annotated_phrase)
        if bookname is not None:
            try:
                reply = get_answer('fact about ' + bookname)
                return reply, self.default_conf
            except BaseException:
                return self.default_reply, 0
        else:
            return self.default_reply, 0

    def __call__(self, dialogs):
        texts = []
        confidences = []
        # GRAMMARLY!!!!!!
        START_PHRASE = "OK, let's talk about books. Do you love reading?"
        NO_PHRASE_1 = "Why don't you love reading?"
        NO_PHRASE_2 = "I imagine that's good for you."
        NO_PHRASE_3 = 'I agree. But there are some better books.'
        NO_PHRASE_4 = "OK, I got it. I suppose you know about it everything you need."
        YES_PHRASE_1 = "That's great. What is the last book you have read?"
        YES_PHRASE_2_NO = "That's OK. I can't name it either."
        YES_PHRASE_2 = "Fabulous! And what book did impress you the most?"
        YES_PHRASE_3_1 = "I've also read it. It's an amazing book!"
        YES_PHRASE_3_FACT = "I've read it. It's an amazing book! Would you like to know some facts about it?"
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
            # TODO check correct order of concatenation of replies
            text_utterances = [j['text'] for j in dialog['utterances']]
            # logging.info('***'.join([j for j in text_utterances]))
            bot_phrases = [j for i, j in enumerate(text_utterances) if i % 2 == 1]
            annotated_user_phrase = dialog['utterances'][-1]
            logging.info(str(annotated_user_phrase))
            # I don't denote annotated_user_phrase['text'].lower() as a single variable
            # in order not to confuse it with annotated_user_phrase
            if any([j in annotated_user_phrase['text'].lower() for j in ['talk about books', 'chat about books']]):
                reply, confidence = START_PHRASE, 1
            elif fact_request_detected(annotated_user_phrase):
                reply, confidence = YES_PHRASE_3_FACT, self.default_conf
            elif YES_PHRASE_3_FACT == bot_phrases[-1]:
                if is_no(annotated_user_phrase):
                    reply, confidence = NO_PHRASE_4, self.default_conf
                elif is_yes(annotated_user_phrase):
                    reply, confidence = self.fact_about_book(annotated_user_phrase)
                else:
                    reply, confidence = self.default_reply, 0
            elif START_PHRASE in bot_phrases:
                if repeat(annotated_user_phrase):
                    reply, confidence = bot_phrases[-1], self.default_conf
                elif is_stop(annotated_user_phrase) or side_intent(annotated_user_phrase):
                    reply, confidence = self.default_reply, 0
                elif START_PHRASE == bot_phrases[-1]:
                    if is_no(annotated_user_phrase):
                        reply, confidence = NO_PHRASE_1, self.default_conf
                    elif is_yes(annotated_user_phrase):
                        reply, confidence = YES_PHRASE_1, self.default_conf
                    else:
                        reply, confidence = self.default_reply, 0
                elif NO_PHRASE_1 == bot_phrases[-1]:
                    reply, confidence = NO_PHRASE_2, self.default_conf
                elif YES_PHRASE_1 == bot_phrases[-1]:
                    if is_no(annotated_user_phrase):
                        reply, confidence = YES_PHRASE_2_NO, self.default_conf
                    else:
                        reply, confidence = parse_author_best_book(annotated_user_phrase,
                                                                   default_phrase=YES_PHRASE_2,
                                                                   default_confidence=self.default_conf)
                elif YES_PHRASE_2 == bot_phrases[-1] or 'Interesting. Have you read ' in bot_phrases[-1]:
                    if is_no(annotated_user_phrase):
                        reply, confidence = NO_PHRASE_2, self.default_conf
                    elif is_yes(annotated_user_phrase) or opinion_expression_detected(annotated_user_phrase):
                        if is_negative(annotated_user_phrase):
                            reply, confidence = NO_PHRASE_3, self.default_conf
                        else:
                            reply, confidence = YES_PHRASE_3_1, self.default_conf
                    else:
                        reply, confidence = self.default_reply, 0
                elif fact_request_detected(annotated_user_phrase):
                    reply, confidence = self.fact_about_book(annotated_user_phrase)

                else:
                    if GENRE_PHRASE_1 not in bot_phrases:
                        reply, confidence = GENRE_PHRASE_1, self.default_conf
                    elif GENRE_PHRASE_1 == bot_phrases[-1]:
                        book = get_genre_book(annotated_user_phrase)
                        if book is None:
                            reply, confidence = self.default_reply, 0
                        else:
                            reply, confidence = GENRE_PHRASE_2(book), self.default_conf
                    elif 'Amazing! Have you read ' in bot_phrases[-1] and 'book' in bot_phrases[-1]:
                        if tell_me_more(annotated_user_phrase):
                            reply = None
                            bookname = bot_phrases[-1].split('book')[1].split('?')[0]
                            bookreads_data = json.load(open(self.bookread_dir, 'r'))[0]
                            for genre in bookreads_data:
                                if bookreads_data[genre]['title'] == bookname:
                                    reply, confidence = bookreads_data[genre]['description'], self.default_conf
                            if reply is None:
                                part1 = 'From bot phrase ' + bot_phrases[-1]
                                part2 = ' bookname *' + bookname + '* didnt match'
                                raise Exception(part1 + part2)
                        elif is_no(annotated_user_phrase):
                            reply, confidence = GENRE_PHRASE_ADVICE, self.default_conf
                        elif is_yes(annotated_user_phrase):
                            if is_positive(annotated_user_phrase):
                                reply, confidence = GENRE_LOVE_PHRASE, self.default_conf
                            elif is_negative(annotated_user_phrase):
                                reply, confidence = GENRE_HATE_PHRASE, self.default_conf
                            else:
                                reply, confidence = GENRE_NOTSURE_PHRASE, self.default_conf

                        else:
                            reply, confidence = self.default_reply, 0
                    elif bot_phrases[-1] == GENRE_NOTSURE_PHRASE:
                        if is_yes(annotated_user_phrase):
                            reply, confidence = GENRE_LOVE_PHRASE, self.default_conf
                        elif is_no(annotated_user_phrase):
                            reply, confidence = GENRE_HATE_PHRASE, self.default_conf
                        else:
                            reply, confidence = self.default_reply, 0
            else:
                reply, confidence = self.default_reply, 0

            assert reply is not None
            texts.append(reply)
            confidences.append(confidence)

        return texts, confidences  # , human_attributes, bot_attributes, attributes
