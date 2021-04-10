import json
import logging
import random
import re
import sentry_sdk
from os import getenv

from common.books import BOOK_SKILL_CHECK_PHRASES, about_book, BOOK_PATTERN
from common.constants import CAN_CONTINUE_SCENARIO, MUST_CONTINUE, CAN_NOT_CONTINUE
from common.tutor import get_tutor_phrase
from common.universal_templates import is_switch_topic, if_chat_about_particular_topic, tell_me_more, \
    is_positive, is_negative
from common.utils import is_yes, is_no
from utils import get_name, get_genre, suggest_template, get_not_given_question_about_books, dontlike, \
    fact_about_book, fav_genre_request_detected, is_side_intent, is_stop, \
    fav_book_request_detected, parse_author_best_book, best_book_by_author, GENRE_PHRASES, was_question_about_book, \
    asked_about_genre, GENRE_DICT, is_previous_was_book_skill, just_mentioned, dontknow


sentry_sdk.init(getenv('SENTRY_DSN'))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

START_PHRASE = "OK, let's talk about books. Do you love reading?"
IF_LOVE_READING = "That's great."
LAST_BOOK_READ = "What is the last book you have read?"
IF_NOT_LOVE_READING = "Why don't you love reading?"
IF_NOT_REMEMBER_LAST_BOOK = "That's OK. I can't name it either."
IF_REMEMBER_LAST_BOOK = "Interesting. Have you read BOOK?"
WHAT_BOOK_IMPRESSED_MOST = "And what book did impress you the most?"
AMAZING_READ_BOOK = "I've read it. It's an amazing book!"
WHEN_IT_WAS_PUBLISHED = "Do you know when it was first published?"
OFFER_FACT_ABOUT_BOOK = "Would you like to know some facts about it?"
OFFER_FACT_DID_NOT_FIND_IT = "Sorry, I suggested the fact but can not find it now."
DID_NOT_EXIST = "I didn't exist in that time."
BOOK_CHANGE_PHRASE = "Okay! What would you like to talk about? For example, movies, games or news."
BOOK_ANY_PHRASE = "I see you can't name it. Could you please name any book you have read?"
FAVOURITE_GENRE_ANSWERS = list(GENRE_PHRASES.values())
FAVOURITE_BOOK_ANSWERS = ['My favourite book is "The Old Man and the Sea" by Ernest Hemingway.',
                          'The Old Man and the Sea tells the story of a battle between a fisherman '
                          'and a large marlin. This is my favourite story, it is truly fascinating.']
WHAT_IS_FAV_GENRE = 'What is your favorite book genre?'

HAVE_YOU_READ_BOOK = 'Amazing! Have you read BOOK? And if you have read it, what do you think about it?'
READ_BOOK_ADVICE = "You can read it. You won't regret it!"
USER_LIKED_BOOK_PHRASE = "I see you love it. It is so wonderful that you read the books you love."
USER_DISLIKED_BOOK_PHRASE = "I see that this book didn't excite you. " \
                            "It's OK. Maybe some other books will fit you better."
OPINION_REQUEST_ON_BOOK_PHRASES = ["Did you enjoy this book?",
                                   "Did you find this book interesting?",
                                   "Was this book exciting for you?"]
UNKNOWN_BOOK_QUESTIONS = ["Sorry I've never heard about this book. What is it about?",
                          "Not sure if I've heard of this book before. What is it about?",
                          "I suppose I've never heard about this book before. What did you like about it?",
                          "Oops. I guess I've never heard about this book before. "
                          "What caught your attention in this book?"]
DONT_KNOW_EITHER = "I don't know either. Let's talk about something else."


class BookSkillScenario:

    def __init__(self):
        self.super_conf = 1.0
        self.default_conf = 0.95
        self.low_conf = 0.7
        self.default_reply = ""
        self.bookreads_dir = 'bookreads_data.json'
        self.bookreads_data = json.load(open(self.bookreads_dir, 'r'))[0]

    def get_genre_book(self, annotated_user_phrase):
        '''
        TODO: Parse genre from phrase and get a book of this genre
        moved here to not load bookreadsd_data everytime but use this one from the class
        '''
        logger.debug('genre book about')
        logger.debug(annotated_user_phrase)
        user_phrase = annotated_user_phrase['text']
        genre = get_genre(user_phrase)
        if genre is None:
            genre = 'fiction'
        book = self.bookreads_data[genre]['title']
        return book

    def genrebook_request_detected(self, annotated_user_phrase):
        phrase = annotated_user_phrase['text'].lower()
        is_genre_in_phrase = any([j in phrase for j in self.bookreads_data.keys()])
        return re.search(suggest_template, annotated_user_phrase['text']) and is_genre_in_phrase

    def get_reply_considering_book_author_genre_info(self, annotated_user_phrase, annotated_prev_phrase):
        logger.debug('Getting whether phrase contains name of author, book or genre')
        author_name, _ = get_name(annotated_user_phrase, 'author')
        bookname, n_years_ago = get_name(annotated_user_phrase, 'book', bookyear=True)
        genre_name = get_genre(annotated_user_phrase['text'], return_name=True)
        if author_name is not None:
            logger.debug(f'Phrase contains name of author {author_name}')
            reply1 = f'I enjoy reading books of {author_name}.'
            best_book = best_book_by_author(author_name, default_phrase=None)
            if best_book is not None:
                reply2 = f'My favourite book of this author is {best_book}.'
            else:
                reply2 = ''
            reply = f"{reply1} {reply2}".strip()
            if author_name.lower() in annotated_user_phrase['text'].lower():
                # if author name is long enough, set super confidence
                confidence = self.super_conf
            else:
                confidence = self.default_conf
        elif bookname is not None:
            logger.debug(f'Phrase contains name of book {bookname}')
            reply = f'{bookname} is an amazing book!'
            if n_years_ago is not None:
                reply = f'{reply} {WHEN_IT_WAS_PUBLISHED}'
            if bookname.lower() in annotated_user_phrase['text'].lower():
                # if bookname is long enough, set super confidence
                confidence = self.super_conf
            else:
                confidence = self.default_conf
        elif genre_name is not None:
            prev_genre = get_genre(annotated_prev_phrase['text'], return_name=True)
            only_one_phrase = len(GENRE_PHRASES[genre_name]) == 1
            logger.debug(f'Phrase contains name of genre {genre_name}')
            if prev_genre != genre_name or only_one_phrase:
                reply = GENRE_PHRASES[genre_name][0]
            else:
                reply = GENRE_PHRASES[genre_name][1]
            if len(genre_name) > 5:
                confidence = self.super_conf
            else:
                confidence = self.default_conf
        else:
            reply, confidence = self.default_reply, 0

        return reply, confidence

    def __call__(self, dialogs):
        texts, confidences = [], []
        human_attrs, bot_attrs, attrs = [], [], []

        for dialog in dialogs:
            reply = ""
            confidence = 0
            attr = {}
            bot_attr = {}
            human_attr = {}
            human_attr["book_skill"] = dialog["human"]["attributes"].get("book_skill", {})
            human_attr['book_skill']['used_phrases'] = human_attr['book_skill'].get('used_phrases', [])
            human_attr['book_skill']['last_fact'] = human_attr['book_skill'].get('last_fact', '')
            try:
                # TODO check correct order of concatenation of replies
                book_just_active = is_previous_was_book_skill(dialog)
                bot_phrases = [j['text'] for j in dialog['bot_utterances']]
                if len(bot_phrases) == 0:
                    bot_phrases.append('')
                    annotated_bot_phrase = {'text': '', 'annotations': {}}
                else:
                    annotated_bot_phrase = dialog['bot_utterances'][-1]
                logger.debug(f'bot phrases: {bot_phrases}')

                user_phrases = [utt["text"] for utt in dialog['human_utterances'][-2:]]
                annotated_user_phrase = dialog['human_utterances'][-1]

                if len(dialog['human_utterances']) > 1:
                    annotated_prev_phrase = dialog['human_utterances'][-2]
                else:
                    annotated_prev_phrase = {'text': ''}

                logger.debug(f'User phrase: last and prev from last: {user_phrases}')
                # I don't denote annotated_user_phrase['text'].lower() as a single variable
                # in order not to confuse it with annotated_user_phrase
                lets_chat_about_books = if_chat_about_particular_topic(
                    annotated_user_phrase, annotated_bot_phrase, compiled_pattern=BOOK_PATTERN)
                if lets_chat_about_books and not is_no(annotated_user_phrase):
                    # let's chat about books
                    logger.debug('Detected talk about books. Calling start phrase')
                    if START_PHRASE in human_attr['book_skill']['used_phrases']:
                        reply = get_not_given_question_about_books(human_attr['book_skill']['used_phrases'])
                        confidence = self.super_conf
                    else:
                        reply, confidence = START_PHRASE, self.super_conf
                elif dontlike(annotated_user_phrase):
                    # no more books OR user doesn't like books
                    logger.debug('DONTLIKE detected')
                    reply, confidence = '', 0
                elif dontknow(annotated_user_phrase):
                    reply, confidence = BOOK_ANY_PHRASE, self.default_conf
                elif book_just_active and is_switch_topic(annotated_user_phrase):
                    # if book skill was active and switch topic intent, offer movies
                    logger.debug('Switching topic')
                    reply, confidence = BOOK_CHANGE_PHRASE, self.default_conf
                elif book_just_active and (is_stop(annotated_user_phrase) or is_side_intent(annotated_user_phrase)):
                    # if book skill was active, stop/not/other intents, do not reply
                    logger.debug('Detected stop/no/other intent')
                    reply, confidence = self.default_reply, 0
                elif fav_genre_request_detected(annotated_user_phrase):
                    # if user asked us about favorite genre
                    logger.debug('Detected favorite genre request')
                    reply, confidence = random.choice(FAVOURITE_GENRE_ANSWERS), self.super_conf
                elif asked_about_genre(annotated_user_phrase):
                    genre_asked = get_genre(annotated_user_phrase)
                    reply, confidence = GENRE_DICT[genre_asked], self.default_conf
                elif fav_book_request_detected(annotated_user_phrase):
                    # if user asked us about favorite book
                    logger.debug('Detected favorite book request')
                    if FAVOURITE_BOOK_ANSWERS[0] not in human_attr['book_skill']['used_phrases']:
                        reply = FAVOURITE_BOOK_ANSWERS[0]
                    elif FAVOURITE_BOOK_ANSWERS[1] not in human_attr['book_skill']['used_phrases']:
                        reply = FAVOURITE_BOOK_ANSWERS[1]
                    else:
                        reply = random.choice(FAVOURITE_BOOK_ANSWERS)
                    confidence = self.super_conf
                elif fav_book_request_detected(annotated_prev_phrase) and tell_me_more(annotated_user_phrase):
                    reply, confidence = FAVOURITE_BOOK_ANSWERS[1], self.super_conf
                elif OFFER_FACT_ABOUT_BOOK in bot_phrases[-1]:
                    # if we offered fact about book on the previous step
                    logger.debug('Previous bot phrase was AMAZING_READ_BOOK & OFFER_FACT_ABOUT_BOOK')
                    if is_yes(annotated_user_phrase):
                        logger.debug('Detected is_yes answer')
                        for phrase in [annotated_user_phrase, annotated_prev_phrase]:
                            # logger.debug(str(phrase))
                            logger.debug('Finding fact about book')
                            reply, confidence = human_attr['book_skill']['last_fact'], self.super_conf
                            if reply is not None:
                                logger.debug('Found a bookfact')
                                break
                        if reply is None:
                            # if we offered fact but didn't find it, say sorry about that
                            logger.debug('Fact about book returned None')
                            reply, confidence = OFFER_FACT_DID_NOT_FIND_IT, self.default_conf
                    elif is_no(annotated_user_phrase):
                        # if user say no, we offer change to movies
                        logger.debug('Offering change to movies')
                        reply, confidence = BOOK_CHANGE_PHRASE, self.default_conf
                    else:
                        # if user said something else on the fact offering, do not answer at all
                        logger.debug('User said sth else on the offered fact')
                        reply, confidence = self.default_reply, 0
                elif START_PHRASE in bot_phrases[-1]:
                    # if we asked do you love reading previously
                    logger.debug('We have just said Do you love reading')
                    if is_no(annotated_user_phrase):
                        logger.debug('Detected answer NO')
                        reply, confidence = IF_NOT_LOVE_READING, self.super_conf
                    elif is_yes(annotated_user_phrase):
                        logger.debug('Detected asnswer YES')
                        reply, confidence = f"{IF_LOVE_READING} {LAST_BOOK_READ}", self.super_conf
                    else:
                        logger.debug('No answer detected. Return nothing.')
                        reply, confidence = self.default_reply, 0
                elif IF_NOT_LOVE_READING in bot_phrases[-1]:
                    # if we said on the previous turn Why don't you love reading
                    logger.debug('We have just said IF_NOT_LOVE_READING')
                    reply, confidence = BOOK_CHANGE_PHRASE, self.default_conf
                elif LAST_BOOK_READ in bot_phrases[-1]:
                    logger.debug('We have just said IF_LOVE_READING LAST_BOOK_READ')
                    if is_no(annotated_user_phrase):
                        # probably user does not remember last read book
                        logger.debug('NO answer detected')
                        reply, confidence = IF_NOT_REMEMBER_LAST_BOOK, self.default_conf
                    else:
                        logger.debug('Does not detect NO. Parsing author best book for')
                        logger.debug(annotated_user_phrase['text'])
                        book = parse_author_best_book(annotated_user_phrase)
                        if book and not just_mentioned(annotated_user_phrase, book):
                            logger.debug('Found_BEST_BOOK')
                            reply = IF_REMEMBER_LAST_BOOK.replace("BOOK", book)
                            confidence = self.default_conf
                        else:
                            logger.debug(f"Best book for {annotated_user_phrase['text']} not retrieved")
                            reply, confidence = f"Fabulous! {WHAT_BOOK_IMPRESSED_MOST}", self.default_conf
                elif WHAT_BOOK_IMPRESSED_MOST in bot_phrases[-1]:
                    logger.debug('We have just said YES_PHRASE_2')
                    if is_no(annotated_user_phrase):
                        logger.debug('NO answer detected')
                        reply, confidence = BOOK_CHANGE_PHRASE, self.default_conf
                    else:
                        logger.debug(f"Did not detect NO answer. Getting name for: {annotated_user_phrase['text']}")
                        bookname, bookyear = get_name(annotated_user_phrase, mode='book', bookyear=True)
                        if bookname is None:
                            logger.debug('No bookname detected: returning default reply')
                            reply, confidence = self.default_reply, 0
                        else:
                            # if we found book name in user reply
                            logger.debug('Bookname detected: returning AMAZING_READ_BOOK & WHEN_IT_WAS_PUBLISHED')
                            reply = f"{AMAZING_READ_BOOK} {WHEN_IT_WAS_PUBLISHED}"
                            if len(bookname.split()) > 2 and bookname.lower() in annotated_user_phrase["text"].lower():
                                # if book title is long enough and is in user reply, set super conf
                                confidence = self.super_conf
                            else:
                                confidence = self.default_conf
                elif WHEN_IT_WAS_PUBLISHED in bot_phrases[-1]:
                    # if we asked when it was published
                    logger.debug(f"We have just asked when the book was published: "
                                 f"getting name for {annotated_prev_phrase['text']}")
                    bookname, n_years_ago = get_name(annotated_prev_phrase, mode='book', bookyear=True)
                    if bookname is None:
                        logger.debug('No bookname detected')
                        reply, confidence = DONT_KNOW_EITHER, self.default_conf
                    else:
                        logger.debug('Bookname detected')
                        if n_years_ago > 0:
                            recency_phrase = f"{n_years_ago} years ago!"
                        else:
                            recency_phrase = 'Just recently!'
                        # answering with default conf as we do not even check the user utterance at all
                        logger.debug('Giving recency phrase')
                        reply, confidence = f"{recency_phrase} {DID_NOT_EXIST} {get_tutor_phrase()}", self.default_conf
                elif bot_phrases[-1] in OPINION_REQUEST_ON_BOOK_PHRASES:
                    # if we previously asked about user's opinion on book
                    logger.debug('Last phrase was OPINION_REQUEST_ON_BOOK_PHRASES')
                    if is_yes(annotated_user_phrase):
                        logger.debug('YES intent detected')
                        reply, confidence = USER_LIKED_BOOK_PHRASE, self.super_conf
                    elif is_no(annotated_user_phrase):
                        logger.debug('NO intent detected')
                        reply, confidence = USER_DISLIKED_BOOK_PHRASE, self.super_conf
                    else:
                        logger.debug('Detected neither YES nor NO intent. Returning nothing')
                        reply, confidence = self.default_reply, 0
                elif WHAT_IS_FAV_GENRE == bot_phrases[-1] or self.genrebook_request_detected(annotated_user_phrase):
                    # push it to the end to move forward variants where we the topic is known
                    logger.debug(f"Last phrase is WHAT_IS_FAV_GENRE for {annotated_user_phrase['text']}")
                    book = self.get_genre_book(annotated_user_phrase)
                    if book is None or is_no(annotated_user_phrase):
                        logger.debug('No book found')
                        reply, confidence = self.default_reply, 0
                    else:
                        # default conf as no check for user uttr (not super conf)
                        logger.debug(f'Returning genre phrase for {book}')
                        reply, confidence = HAVE_YOU_READ_BOOK.replace("BOOK", book), self.default_conf
                elif HAVE_YOU_READ_BOOK in bot_phrases[-1]:
                    logger.debug('"Amazing! Have HAVE_YOU_READ_BOOK in last bot phrase')
                    if tell_me_more(annotated_user_phrase):
                        logger.debug('Tell me more intent detected')
                        reply = None
                        bookname = bot_phrases[-1].split('you read ')[1].split('?')[0].strip()
                        logger.debug(f'Detected name {bookname} in last_bot_phrase')
                        for genre in self.bookreads_data:
                            if self.bookreads_data[genre]['title'] == bookname:
                                logger.debug(f'Returning phrase for book of genre {genre}')
                                # as we checked user utter as tell me more, we assign super conf
                                reply, confidence = self.bookreads_data[genre]['description'], self.super_conf
                        if reply is None:
                            part1 = f'From bot phrase {bot_phrases[-1]}'
                            part2 = f' bookname * bookname * didnt match'
                            sentry_sdk.capture_exception(Exception(part1 + part2))
                            logger.exception(part1 + part2)
                            reply, confidence = self.default_reply, 0
                    elif is_no(annotated_user_phrase):
                        logger.debug('intent NO detected')
                        reply, confidence = READ_BOOK_ADVICE, self.super_conf
                    elif is_yes(annotated_user_phrase):
                        logger.debug('YES intent detected')
                        if is_positive(annotated_user_phrase):
                            logger.debug('positive intent detected')
                            reply, confidence = USER_LIKED_BOOK_PHRASE, self.super_conf
                        elif is_negative(annotated_user_phrase):
                            logger.debug('negative intent detected')
                            reply, confidence = USER_DISLIKED_BOOK_PHRASE, self.super_conf
                        else:
                            logger.debug('Without detected intent returning OPINION_REQUEST_ON_BOOK_PHRASES')
                            reply, confidence = random.choice(OPINION_REQUEST_ON_BOOK_PHRASES), self.default_conf
                    else:
                        logger.debug('No intent detected. Returning nothing')
                        reply, confidence = self.default_reply, 0
                elif any([phrase in bot_phrases[-1] for phrase in BOOK_SKILL_CHECK_PHRASES]):
                    logger.debug('Reply considering book genre')
                    reply, confidence = self.get_reply_considering_book_author_genre_info(
                        annotated_user_phrase, annotated_prev_phrase)
                    if confidence == 0:
                        logger.debug('An unknown book met')
                        reply, confidence = random.choice(UNKNOWN_BOOK_QUESTIONS), self.low_conf
                elif about_book(annotated_user_phrase):
                    bookname, n_years_ago = get_name(annotated_user_phrase, mode='book', bookyear=True)
                    if bookname is None:
                        logger.debug('No bookname detected')
                        if WHAT_IS_FAV_GENRE not in human_attr['book_skill']['used_phrases']:
                            logger.debug('WHAT_IS_FAV_GENRE not in bot phrases: returning it')
                            reply, confidence = WHAT_IS_FAV_GENRE, self.default_conf
                        else:
                            reply, confidence = "", 0
                    else:
                        retrieved_fact = fact_about_book(annotated_user_phrase)
                        if retrieved_fact is not None and was_question_about_book(annotated_user_phrase):
                            # if user asked ANY question about books, answer with fact.
                            # BUT not with the super confidence,
                            # because actually factoid/cobotqa can give exact answer to the user's question
                            logger.debug('Detected fact request')
                            reply, confidence = f"{AMAZING_READ_BOOK} {OFFER_FACT_ABOUT_BOOK}", self.default_conf
                            human_attr['book_skill']['last_fact'] = retrieved_fact
                        else:
                            logger.debug('Was question about book but fact not retrieved')
                            reply, confidence = self.default_reply, 0
                    if reply == "":
                        reply, confidence = self.get_reply_considering_book_author_genre_info(
                            annotated_user_phrase, annotated_prev_phrase)
                else:
                    logger.debug('Final branch')
                    reply, confidence = self.default_reply, 0
                if confidence == self.super_conf:
                    attr = {"can_continue": MUST_CONTINUE}
                elif confidence == self.default_conf:
                    attr = {"can_continue": CAN_CONTINUE_SCENARIO}
                else:
                    attr = {'can_continue': CAN_NOT_CONTINUE}
            except Exception as e:
                logger.exception("exception in book skill")
                sentry_sdk.capture_exception(e)
                reply = ""
                confidence = 0

            if isinstance(reply, list):
                reply = " ".join(reply)
            if reply in human_attr['book_skill']['used_phrases']:
                confidence *= 0.9
            texts.append(reply)
            if len(reply) > 0:
                human_attr['book_skill']['used_phrases'].append(reply)
            confidences.append(confidence)
            human_attrs.append(human_attr)
            attrs.append(attr)
            bot_attrs.append(bot_attr)

        return texts, confidences, human_attrs, bot_attrs, attrs
