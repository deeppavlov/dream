import json
import logging
import random
import re
import datetime
import sentry_sdk
from os import getenv

from common.books import BOOK_SKILL_CHECK_PHRASES, about_book, BOOK_PATTERN, ASK_TO_REPEAT_BOOK
from common.constants import CAN_CONTINUE_SCENARIO, MUST_CONTINUE, CAN_NOT_CONTINUE
from common.gaming import ALL_LINKS_TO_BOOKS
from common.universal_templates import is_switch_topic, if_chat_about_particular_topic, tell_me_more, \
    is_positive, is_negative
from common.utils import is_yes, is_no, entity_to_label
from book_utils import get_name, get_genre, suggest_template, get_not_given_question_about_books, dontlike_books, \
    fact_about_book, fav_genre_request_detected, is_side_intent, is_stop, genre_of_book, get_published_year, \
    parse_author_best_book, GENRE_PHRASES, was_question_about_book, favorite_book_template, exit_skill, \
    asked_about_genre, GENRE_DICT, is_previous_was_book_skill, just_mentioned, dontknow_books, \
    best_plain_book_by_author, tell_about_genre_book, bible_request, get_movie_answer, \
    my_favorite, get_author, what_is_book_about, havent_read, is_wikidata_entity, published_year_request

sentry_sdk.init(getenv('SENTRY_DSN'))

logger = logging.getLogger(__name__)

ASK_GENRE_OF_BOOK = "Do you know what is the genre of this book?"
GENRE_ADVICE_PHRASE = "By the way, may I advice you a book from this genre?"
START_PHRASE = "OK, let's talk about books. Books are my diamonds. Do you love reading?"
IF_LOVE_READING = "That's great. Outside of a dog, a book is a man's best friend."
LAST_BOOK_READ = "What is the last book you have read?"
IF_NOT_LOVE_READING = "Why don't you love reading? Maybe you haven't found the right book?"
IF_NOT_REMEMBER_LAST_BOOK = "That's OK. I can't name it either."
IF_REMEMBER_LAST_BOOK = "You have a great taste in books! " \
                        "I also adore books of AUTHOR, especially BOOK."
ASK_WHY = "Why do you enjoy reading?"
ASK_ABOUT_OFFERED_BOOK = "It's a real showpiece. Have you read it?"
TELL_REQUEST = " May I tell you something about this book?"
TELL_REQUEST2 = " May I tell you something else about this book?"
WHAT_BOOK_IMPRESSED_MOST = "what book did impress you the most?"
AMAZING_READ_BOOK = "I've read it. It's an amazing book!"
AMAZING_READ_BOOK_EXPANDED = "I've read it. It's truly a masterpiece of AUTHOR!"
ACKNOWLEDGE_AUTHOR = "AUTHOR is a wonderful writer."
ASK_GENRE_ABOUT_AUTHOR = "Do you know in what genre this author wrote?"
WHEN_IT_WAS_PUBLISHED = "Do you know when it was first published?"
OFFER_FACT_ABOUT_BOOK = "Would you like to know some facts about it?"
OFFER_FACT_DID_NOT_FIND_IT = "Sorry, I suggested the fact but can not find it now."
PROPOSE_FAVOURITE_BOOK = 'Do you want to know what my favourite book is?'
DID_NOT_EXIST = "I didn't exist in that time."
BOOK_ANY_PHRASE = "I see you can't name it. Could you please name any book you have read?"
FAVOURITE_GENRE_ANSWERS = list(GENRE_PHRASES.values())
FAVOURITE_BOOK_ANSWERS = [f'My favourite book is "The catcher in the rye" by J. D. Salinger. {TELL_REQUEST}',
                          f'The novel "The catcher in the rye" tells the story of a teenager '
                          f'who has been kicked out of a boarding school.'
                          f'This is my favourite story, it is truly fascinating. {TELL_REQUEST2}']
WHAT_IS_FAV_GENRE = 'I have read a plenty of books from different genres. What book genre do you like?'
ASK_ABOUT_GENRE_BOOK = 'And if you have read it, what do you think about it?'
HAVE_YOU_READ_BOOK = f'Amazing! Have you read BOOK? {ASK_ABOUT_GENRE_BOOK}'
BIBLE_RESPONSES = ["I know that Bible is one of the most widespread books on the Earth. "
                   "It forms the basic of the Christianity. Have you read the whole Bible?",
                   "Unfortunately, as a socialbot, I don't have an immortal soul,"
                   "so I don't think I will ever get into Heaven. That's why I don't know much about religion."]
READ_BOOK_ADVICE = "You can read it. You won't regret it!"
USER_LIKED_BOOK_PHRASE = "I see you love it. It is so wonderful that you read the books you love."
USER_DISLIKED_BOOK_PHRASE = "It's OK. Maybe some other books will fit you better."
OPINION_REQUEST_ON_BOOK_PHRASES = ["Did you enjoy this book?",
                                   "Did you find this book interesting?",
                                   "Was this book exciting for you?"]
BOOK_ACKNOWLEDGEMENT_PHRASE = 'Never heard about it. Is it a book, an author or a genre?'
WILL_CHECK = 'OK, I will check it out later.'
DONT_KNOW_EITHER = "I don't know either. Let's talk about something else."
QUESTIONS_ABOUT_BOOK = [BOOK_ANY_PHRASE, LAST_BOOK_READ, WHAT_BOOK_IMPRESSED_MOST, BOOK_ACKNOWLEDGEMENT_PHRASE] \
    + BOOK_SKILL_CHECK_PHRASES + ALL_LINKS_TO_BOOKS
CURRENT_YEAR = datetime.datetime.today().year


class BookSkillScenario:

    def __init__(self):
        self.super_conf = 1.0
        self.default_conf = 0.95
        self.low_conf = 0.7
        self.default_reply = ""
        self.bookreads_dir = 'bookreads_data.json'
        self.bookreads_data = json.load(open(self.bookreads_dir, 'r'))[0]
        self.bookreads_books = [book['title'] for books in self.bookreads_data.values() for book in books]

    def get_genre_book(self, annotated_user_phrase, human_attr):
        '''
        TODO: Parse genre from phrase and get a book of this genre
        moved here to not load bookreadsd_data everytime but use this one from the class
        '''
        logger.debug('genre book about')
        logger.debug(annotated_user_phrase)
        user_phrase = annotated_user_phrase['text']
        genre = get_genre(user_phrase)
        if genre is None:
            genre = human_attr['book_skill'].get('detected_genre', None)
        if genre:
            human_attr['book_skill']['detected_genre'] = None  # reset attribute
        else:  # default genre
            genre = 'fiction'
        for book_info in self.bookreads_data[genre]:
            book = book_info['title']
            if book not in human_attr['book_skill']['used_genrebooks']:
                human_attr['book_skill']['used_genrebooks'].append(book)
                return book

    def fav_book_request_detected(self, annotated_user_phrase, last_bot_phrase, human_attr):
        user_asked_favourite_book = re.search(favorite_book_template, annotated_user_phrase["text"])
        bot_proposed_favourite_book = any([k in last_bot_phrase
                                           for k in [PROPOSE_FAVOURITE_BOOK, FAVOURITE_BOOK_ANSWERS[0]]])
        not_finished = FAVOURITE_BOOK_ANSWERS[1] not in human_attr['book_skill']['used_phrases']
        user_agreed = is_yes(annotated_user_phrase)
        return user_asked_favourite_book or (bot_proposed_favourite_book and user_agreed) and not_finished

    def genrebook_request_detected(self, annotated_user_phrase, bot_phrases):
        was_bot_phrase = any([j in bot_phrases[-1] for j in [ASK_GENRE_ABOUT_AUTHOR, WHAT_IS_FAV_GENRE]])
        we_suggested_genre = GENRE_ADVICE_PHRASE in bot_phrases[-1]
        phrase = annotated_user_phrase['text'].lower()
        is_genre_in_phrase = any([j in phrase for j in self.bookreads_data.keys()])
        user_asked_to_recommend_book = (
            re.search(suggest_template, annotated_user_phrase['text']) and is_genre_in_phrase)
        user_agreed_to_recommend_book = is_yes(annotated_user_phrase) and we_suggested_genre
        return was_bot_phrase or is_genre_in_phrase or user_asked_to_recommend_book or user_agreed_to_recommend_book

    def reply_about_book(self, annotated_user_phrase, human_attr, yes_function=is_yes,
                         no_function=is_no, default_phrases=['']):
        if yes_function(annotated_user_phrase):
            reply, confidence = USER_LIKED_BOOK_PHRASE, self.super_conf
        elif no_function(annotated_user_phrase):
            reply, confidence = USER_DISLIKED_BOOK_PHRASE, self.super_conf
        else:
            logger.debug('Detected neither YES nor NO intent. Returning nothing')
            reply, confidence = random.choice(default_phrases), self.default_conf
        if all([human_attr['book_skill'].get('named_favourite', False),
                reply not in default_phrases]):
            reply = f'{reply} {PROPOSE_FAVOURITE_BOOK}'
        elif all([human_attr['book_skill'].get('we_asked_genre', False),
                  reply not in default_phrases]):
            reply = f"{reply} {WHAT_IS_FAV_GENRE}"
            human_attr['book_skill']['we_asked_genre'] = True
        return reply, confidence

    def get_author_book_genre_movie_reply(self, annotated_user_phrase,
                                          annotated_prev_phrase, bot_phrases, human_attr):
        logger.debug('Getting whether phrase contains name of author, book or genre')
        plain_author_name, _ = get_name(annotated_user_phrase, 'author', return_plain=True)
        plain_bookname, n_years_ago = get_name(annotated_user_phrase, 'book', bookyear=True, return_plain=True)
        movie_name, _ = get_name(annotated_user_phrase, mode='movie')
        genre_name = get_genre(annotated_user_phrase['text'], return_name=True)
        nothing_found = not genre_name and not movie_name and not n_years_ago and not is_wikidata_entity(
            plain_author_name)
        we_asked_about_book = any([phrase in bot_phrases[-1]
                                   for phrase in QUESTIONS_ABOUT_BOOK])
        if we_asked_about_book and nothing_found:
            if BOOK_ACKNOWLEDGEMENT_PHRASE != bot_phrases[-1]:
                reply, confidence = BOOK_ACKNOWLEDGEMENT_PHRASE, self.default_conf
                was_book_acknowledgement = any([BOOK_ACKNOWLEDGEMENT_PHRASE in j
                                                for j in human_attr['book_skill']['used_phrases']])
                if was_book_acknowledgement:
                    confidence = 0.5 * confidence
            elif all([WHAT_BOOK_IMPRESSED_MOST not in j for j in human_attr['book_skill']['used_phrases']]):
                reply, confidence = f'{WILL_CHECK} By the way, {WHAT_BOOK_IMPRESSED_MOST}', self.default_conf
            elif not human_attr['book_skill'].get('we_asked_genre', False):
                reply, confidence = f'{WILL_CHECK} By the way, {WHAT_IS_FAV_GENRE}', self.default_conf
            else:
                reply, confidence = '', 0
        elif is_wikidata_entity(plain_author_name):
            author_name = entity_to_label(plain_author_name)
            logger.debug('Authorname found')
            plain_book, _ = parse_author_best_book(annotated_user_phrase)
            if is_wikidata_entity(plain_book):
                book = entity_to_label(plain_book)
                if book and not just_mentioned(annotated_user_phrase, book):
                    logger.debug('Found_BEST_BOOK')
                    reply = IF_REMEMBER_LAST_BOOK.replace("BOOK", book).replace('AUTHOR', author_name)
                    human_attr['book_skill']['plain_book'] = plain_book
                    human_attr['book_skill']['n_years_ago'] = CURRENT_YEAR - get_published_year(plain_book)
                    human_attr['book_skill']['book'] = book
                    human_attr['book_skill']['author'] = author_name
                    reply = f'{reply} {ASK_ABOUT_OFFERED_BOOK}'
                    confidence = self.super_conf
            else:
                reply, confidence = f'{ACKNOWLEDGE_AUTHOR} {ASK_GENRE_ABOUT_AUTHOR}', self.default_conf
                reply = reply.replace('AUTHOR', author_name)
        elif is_wikidata_entity(plain_bookname) and n_years_ago:
            # if we found book name in user reply
            bookname = entity_to_label(plain_bookname)
            human_attr['book_skill']['n_years_ago'] = n_years_ago
            human_attr['book_skill']['book'] = bookname
            human_attr['book_skill']['plain_book'] = plain_bookname
            logger.debug('Bookname detected: returning AMAZING_READ_BOOK & WHEN_IT_WAS_PUBLISHED')

            plain_author = get_author(plain_bookname, return_plain=True)
            if is_wikidata_entity(plain_author):
                logger.debug('Is author')
                author_name = entity_to_label(plain_author)
                human_attr['book_skill']['author'] = author_name
                offered_plain_bookname = best_plain_book_by_author(plain_author_name=plain_author,
                                                                   plain_last_bookname=plain_bookname,
                                                                   default_phrase='')
                if is_wikidata_entity(plain_bookname):
                    offered_bookname = entity_to_label(offered_plain_bookname)
                    reply = f"{IF_REMEMBER_LAST_BOOK} {ASK_ABOUT_OFFERED_BOOK}"
                    reply = reply.replace('AUTHOR', author_name).replace('BOOK', offered_bookname)
                else:
                    reply = f"{AMAZING_READ_BOOK} {WHEN_IT_WAS_PUBLISHED}"
            else:
                reply = f"{AMAZING_READ_BOOK} {WHEN_IT_WAS_PUBLISHED}"

            if len(bookname.split()) > 2 and bookname.lower() in annotated_user_phrase['text'].lower():
                # if book title is long enough and is in user reply,we set super conf
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
            if len(genre_name) > 5 and reply not in human_attr['book_skill']['used_phrases']:
                confidence = self.super_conf
            else:
                confidence = self.default_conf
        elif movie_name:
            reply, confidence = get_movie_answer(annotated_user_phrase, human_attr), self.default_conf
        else:
            if any([WHAT_BOOK_IMPRESSED_MOST in j for j in human_attr['book_skill']['used_phrases']]):
                reply, confidence = self.default_reply, 0
            else:
                reply, confidence = f"Fabulous! And {WHAT_BOOK_IMPRESSED_MOST}", self.default_conf
        return reply, confidence, human_attr

    def __call__(self, dialogs):
        texts, confidences = [], []
        human_attrs, bot_attrs, attrs = [], [], []

        for dialog in dialogs:
            reply = ""
            confidence = 0
            attr = {}
            bot_attr = {}
            human_attr = dialog["human"]["attributes"]
            human_attr["book_skill"] = dialog["human"]["attributes"].get("book_skill", {})
            human_attr['book_skill']['used_phrases'] = human_attr['book_skill'].get('used_phrases', [])
            human_attr['book_skill']['last_fact'] = human_attr['book_skill'].get('last_fact', '')
            human_attr['book_skill']['used_genrebooks'] = human_attr['book_skill'].get('used_genrebooks', [])
            try:
                # TODO check correct order of concatenation of replies
                book_just_active = is_previous_was_book_skill(dialog)
                bot_phrases = [j['text'] for j in dialog['bot_utterances']]
                if len(bot_phrases) == 0:
                    bot_phrases.append('')
                    annotated_bot_phrase = {'text': '', 'annotations': {}}
                else:
                    annotated_bot_phrase = dialog['bot_utterances'][-1]
                bot_phrases = [phrase for phrase in bot_phrases if '#repeat' not in phrase]
                logger.debug(f'bot phrases: {bot_phrases}')

                user_phrases = [utt["text"] for utt in dialog['human_utterances'][-2:]]
                logger.info(f"Input received: {user_phrases[-1]}")
                annotated_user_phrase = dialog['human_utterances'][-1]
                genre_detected = get_genre(annotated_user_phrase)
                yes_or_no = is_yes(annotated_user_phrase) or is_no(annotated_user_phrase)
                questions_about_book = [BOOK_ANY_PHRASE, LAST_BOOK_READ,
                                        WHAT_BOOK_IMPRESSED_MOST] + BOOK_SKILL_CHECK_PHRASES
                we_asked_about_book = any([question in bot_phrases[-1] for question in questions_about_book])
                if len(dialog['human_utterances']) > 1:
                    annotated_prev_phrase = dialog['human_utterances'][-2]
                else:
                    annotated_prev_phrase = {'text': ''}

                logger.debug(f'User phrase: last and prev from last: {user_phrases}')
                # I don't denote annotated_user_phrase['text'].lower() as a single variable
                # in order not to confuse it with annotated_user_phrase
                should_stop = any([IF_NOT_LOVE_READING in bot_phrases[-1],
                                   book_just_active and is_switch_topic(annotated_user_phrase),
                                   book_just_active and is_stop(annotated_user_phrase),
                                   book_just_active and is_side_intent(annotated_user_phrase),
                                   dontlike_books(annotated_user_phrase),
                                   we_asked_about_book and is_no(annotated_user_phrase)])
                lets_chat_about_books = if_chat_about_particular_topic(
                    annotated_user_phrase, annotated_bot_phrase, compiled_pattern=BOOK_PATTERN)
                if lets_chat_about_books and not is_no(annotated_user_phrase) and not book_just_active:
                    # let's chat about books
                    logger.debug('Detected talk about books. Calling start phrase')
                    if START_PHRASE in human_attr['book_skill']['used_phrases']:
                        reply = get_not_given_question_about_books(human_attr['book_skill']['used_phrases'])
                        confidence = self.default_conf
                    else:
                        reply, confidence = START_PHRASE, self.super_conf
                elif should_stop:
                    reply, confidence = '', 0
                elif dontknow_books(annotated_user_phrase) and BOOK_ANY_PHRASE not in bot_phrases and book_just_active:
                    reply, confidence = BOOK_ANY_PHRASE, self.default_conf
                elif ASK_WHY in bot_phrases[-1]:
                    reply, confidence = f"{IF_LOVE_READING} {LAST_BOOK_READ}", self.default_conf
                elif my_favorite(annotated_user_phrase) == 'genre':
                    reply, confidence, human_attr = self.get_author_book_genre_movie_reply(annotated_user_phrase,
                                                                                           annotated_prev_phrase,
                                                                                           bot_phrases,
                                                                                           human_attr)
                elif my_favorite(annotated_user_phrase) == 'book':
                    reply, confidence = f'So {WHAT_BOOK_IMPRESSED_MOST}', self.default_conf
                elif fav_genre_request_detected(annotated_user_phrase):
                    # if user asked us about favorite genre
                    logger.debug('Detected favorite genre request')
                    reply, confidence = random.choice(FAVOURITE_GENRE_ANSWERS), self.super_conf
                elif asked_about_genre(annotated_user_phrase) and genre_detected:
                    reply, confidence = GENRE_DICT[genre_detected], self.default_conf
                    reply = f'{reply} {GENRE_ADVICE_PHRASE}'
                    human_attr['book_skill']['detected_genre'] = genre_detected
                elif all([bible_request(annotated_user_phrase),
                          BIBLE_RESPONSES[0] not in human_attr['book_skill']['used_phrases']]):
                    reply, confidence = BIBLE_RESPONSES[0], self.default_conf
                elif any([bible_request(annotated_user_phrase),
                          (bible_request(annotated_prev_phrase) and yes_or_no)]):
                    reply = BIBLE_RESPONSES[1]
                    if BIBLE_RESPONSES[0] == annotated_bot_phrase['text']:
                        reply = f"I am pleased to know it. {reply}"
                    book_question = get_not_given_question_about_books(human_attr['book_skill']['used_phrases'])
                    reply = f'{reply} Apart from the Bible, {book_question}'
                    confidence = self.default_conf
                elif self.fav_book_request_detected(annotated_user_phrase, bot_phrases[-1], human_attr):
                    # if user asked us about favorite book
                    logger.debug('Detected favorite book request')
                    if FAVOURITE_BOOK_ANSWERS[0] not in human_attr['book_skill']['used_phrases']:
                        human_attr['book_skill']['named_favourite'] = True
                        reply = FAVOURITE_BOOK_ANSWERS[0]
                        human_attr['book_skill']['plain_book'] = 'Q183883'
                        human_attr['book_skill']['n_years_ago'] = CURRENT_YEAR - 1951
                        human_attr['book_skill']['book'] = "The Catcher in the Rye"
                        human_attr['book_skill']['author'] = "Jerome Salinger"
                    else:
                        reply = FAVOURITE_BOOK_ANSWERS[1]
                        # TODO in next PRs: behave proactively about this book, propose to discuss it next
                    confidence = self.super_conf
                elif START_PHRASE in bot_phrases[-1]:
                    # if we asked do you love reading previously
                    logger.debug('We have just said Do you love reading')
                    if is_no(annotated_user_phrase):
                        logger.debug('Detected answer NO')
                        reply, confidence = IF_NOT_LOVE_READING, self.super_conf
                    elif is_yes(annotated_user_phrase):
                        logger.debug('Detected asnswer YES')
                        reply, confidence = f"{ASK_WHY}", self.super_conf
                    else:
                        logger.debug('No answer detected. Return nothing.')
                        reply, confidence = self.default_reply, 0
                elif any([phrase in bot_phrases[-1] for phrase in QUESTIONS_ABOUT_BOOK]):
                    reply, confidence, human_attr = self.get_author_book_genre_movie_reply(annotated_user_phrase,
                                                                                           annotated_prev_phrase,
                                                                                           bot_phrases,
                                                                                           human_attr)
                elif WHEN_IT_WAS_PUBLISHED in bot_phrases[-1] or published_year_request(annotated_user_phrase):
                    if 'n_years_ago' in human_attr['book_skill']:
                        n_years_ago = human_attr['book_skill']['n_years_ago']
                        plain_bookname = human_attr['book_skill']['plain_book']
                        bookname = human_attr['book_skill']['book']
                        logger.debug('Bookname detected')
                        if n_years_ago > 0:
                            recency_phrase = f"{n_years_ago} years ago!"
                        else:
                            recency_phrase = 'Just recently!'
                        # answering with default conf as we do not even check the user utterance at all
                        logger.debug('Giving recency phrase')
                        book_genre = genre_of_book(plain_bookname)
                        reply = f"{recency_phrase} {DID_NOT_EXIST}"
                        if book_genre:
                            reply = f"{reply} {ASK_GENRE_OF_BOOK}"
                            reply = reply.replace('BOOK', bookname)
                            human_attr['book_skill']['genre'] = book_genre
                        elif not human_attr['book_skill'].get('we_asked_genre', False):
                            reply = f"{reply} {WHAT_IS_FAV_GENRE}"
                            human_attr['book_skill']['we_asked_genre'] = True
                        else:
                            reply = exit_skill(reply, human_attr)
                        confidence = self.default_conf
                    else:
                        reply, confidence = ASK_TO_REPEAT_BOOK, self.low_conf
                elif bot_phrases[-1] in OPINION_REQUEST_ON_BOOK_PHRASES:
                    # if we previously asked about user's opinion on book
                    reply, confidence = self.reply_about_book(annotated_user_phrase, human_attr,
                                                              is_yes, is_no, [''])
                elif ASK_GENRE_OF_BOOK in bot_phrases[-1] and 'genre' in human_attr['book_skill']:
                    book, genre = human_attr['book_skill']['book'], human_attr['book_skill']['genre']
                    reply, confidence = f"{book} is {genre}. ", self.default_conf
                    if not human_attr['book_skill'].get('we_asked_genre', False):
                        reply = f"{reply} {WHAT_IS_FAV_GENRE}"
                        human_attr['book_skill']['we_asked_genre'] = True
                    elif not human_attr['book_skill'].get('named_favourite', False):
                        reply = f"{reply} {PROPOSE_FAVOURITE_BOOK}"
                    else:
                        reply = exit_skill(reply, human_attr)
                elif self.genrebook_request_detected(annotated_user_phrase,
                                                     bot_phrases):
                    # push it to the end to move forward variants where we the topic is known
                    logger.debug(f"Last phrase is WHAT_IS_FAV_GENRE for {annotated_user_phrase['text']}")
                    book = self.get_genre_book(annotated_user_phrase, human_attr)
                    if book and not is_no(annotated_user_phrase):
                        logger.debug(f'Making genre request')
                        reply, confidence = HAVE_YOU_READ_BOOK.replace("BOOK", book), self.default_conf
                        human_attr['book_skill']['book'] = book
                    else:
                        reply, confidence, human_attr = self.get_author_book_genre_movie_reply(annotated_user_phrase,
                                                                                               annotated_prev_phrase,
                                                                                               bot_phrases,
                                                                                               human_attr)
                elif any([k in bot_phrases[-1] for k in [ASK_ABOUT_OFFERED_BOOK,
                                                         OFFER_FACT_ABOUT_BOOK, ASK_ABOUT_GENRE_BOOK]]):
                    # book_just_offered
                    bookname = human_attr['book_skill']['book']
                    logger.debug('Amazing! Have HAVE_YOU_READ_BOOK in last bot phrase')
                    if tell_me_more(annotated_user_phrase) and bookname in self.bookreads_books:
                        reply = tell_about_genre_book(bookname, self.bookreads_data)
                        if not human_attr['book_skill'].get('named_favourite', False) and reply:
                            reply = f'{reply} {PROPOSE_FAVOURITE_BOOK}'
                            confidence = self.super_conf
                        else:
                            reply = exit_skill(reply, human_attr)
                            confidence = self.default_conf
                    elif is_no(annotated_user_phrase) or havent_read(annotated_user_phrase):
                        logger.debug('intent NO detected')
                        reply, confidence = f'{READ_BOOK_ADVICE} {TELL_REQUEST}', self.super_conf
                    elif is_yes(annotated_user_phrase):
                        reply, confidence = self.reply_about_book(annotated_user_phrase, human_attr,
                                                                  is_positive, is_negative,
                                                                  OPINION_REQUEST_ON_BOOK_PHRASES)
                    else:
                        logger.debug('No intent detected. Returning nothing')
                        if not ([PROPOSE_FAVOURITE_BOOK in phrase
                                 for phrase in human_attr['book_skill']['used_phrases']]):
                            reply, confidence = PROPOSE_FAVOURITE_BOOK, self.default_conf
                        else:
                            reply, confidence = '', -0
                elif len(bot_phrases) >= 1 and any([k in bot_phrases[-1] for k in [TELL_REQUEST, TELL_REQUEST2]]):
                    # We have offered information about book
                    plain_bookname = human_attr['book_skill'].get('plain_book', '')
                    bookname = human_attr['book_skill']['book']
                    logger.debug(f'TELL_REQUEST with {bookname} {plain_bookname}')
                    if (tell_me_more(annotated_user_phrase) or is_yes(annotated_user_phrase)) and bookname:
                        logger.debug('Tell_me_more or is_yes and bookname')
                        reply = tell_about_genre_book(bookname, self.bookreads_data)
                        if reply:
                            if not human_attr['book_skill'].get('named_favourite', False):
                                reply = f'{reply} {PROPOSE_FAVOURITE_BOOK}'
                                confidence = self.super_conf
                            else:
                                reply = exit_skill(reply, human_attr)
                                confidence = self.default_conf
                        elif plain_bookname:
                            book_fact = what_is_book_about(plain_bookname)
                            if book_fact:
                                reply = f'{book_fact} {WHEN_IT_WAS_PUBLISHED}'
                                confidence = self.super_conf
                            else:
                                reply = f'{WHEN_IT_WAS_PUBLISHED}'
                                confidence = self.default_conf
                            #  запускаем в сценарий дальше
                        else:
                            warning_message = 'Either plain_bookname or genre book should be. Check the code'
                            sentry_sdk.capture_exception(warning_message)
                            logger.exception(warning_message)
                            if not human_attr['book_skill'].get('named_favourite', False):
                                reply = f'{PROPOSE_FAVOURITE_BOOK}'
                                confidence = self.default_conf
                            else:
                                reply, confidence = '', 0
                    elif is_no(annotated_user_phrase):
                        reply = 'OK, as you wish.'
                        reply = exit_skill(reply, human_attr)
                        confidence = self.low_conf
                    else:
                        reply, confidence = '', 0
                elif about_book(annotated_user_phrase):
                    plain_bookname, n_years_ago = get_name(annotated_user_phrase, mode='book', bookyear=True,
                                                           return_plain=True)
                    if not is_wikidata_entity(plain_bookname):
                        logger.debug('No bookname detected')
                        movie_name, _ = get_name(annotated_user_phrase, mode='movie')
                        if movie_name:
                            logger.debug('Moviename detected')
                            reply, confidence = get_movie_answer(annotated_user_phrase, human_attr), self.default_conf
                        elif not human_attr['book_skill'].get('we_asked_genre', False):
                            logger.debug('WHAT_IS_FAV_GENRE not in bot phrases: returning it')
                            reply, confidence = WHAT_IS_FAV_GENRE, self.default_conf
                            human_attr['book_skill']['we_asked_genre'] = True
                        else:
                            logger.debug('We are over - finish')
                            reply = exit_skill(reply, human_attr)
                            confidence = self.default_conf
                    else:
                        bookname = entity_to_label(plain_bookname)
                        human_attr['book_skill']['book'] = bookname
                        human_attr['book_skill']['plain_book'] = plain_bookname
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
                        reply, confidence, human_attr = self.get_author_book_genre_movie_reply(annotated_user_phrase,
                                                                                               annotated_prev_phrase,
                                                                                               bot_phrases,
                                                                                               human_attr)
                else:
                    logger.debug('Final branch')
                    if book_just_active:
                        reply = exit_skill(reply, human_attr)
                        confidence = self.default_conf
                    else:
                        reply, confidence = self.default_reply, 0
                if confidence == self.super_conf:
                    attr = {"can_continue": MUST_CONTINUE}
                elif confidence == self.default_conf:
                    attr = {"can_continue": CAN_CONTINUE_SCENARIO}
                else:
                    attr = {"can_continue": CAN_NOT_CONTINUE}
            except Exception as e:
                logger.exception("exception in book skill")
                sentry_sdk.capture_exception(e)
                reply = ""
                confidence = 0

            if isinstance(reply, list):
                reply = " ".join(reply)
            if reply in human_attr['book_skill']['used_phrases']:
                confidence *= 0.95
            texts.append(reply)
            if reply:
                human_attr['book_skill']['used_phrases'].append(reply)
            confidences.append(confidence)
            human_attrs.append(human_attr)
            attrs.append(attr)
            bot_attrs.append(bot_attr)

        return texts, confidences, human_attrs, bot_attrs, attrs
