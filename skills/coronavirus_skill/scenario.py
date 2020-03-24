import logging
from os import getenv
import sentry_sdk
import requests
from string import punctuation
from word2number.w2n import word_to_num
from random import random
sentry_sdk.init(getenv('SENTRY_DSN'))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
CORONAVIRUS_URL = 'https://www.worldometers.info/coronavirus/coronavirus-cases/'
STATES_URL = 'https://edition.cnn.com/2020/03/03/health/us-coronavirus-cases-state-by-state/index.html'
STATES = {j.strip().lower().split(';')[0]: j.strip().lower().split(';')[1]
          for j in open('state_names.txt', 'r').readlines()}
FACT_LIST = ['The children are almost invincible for coronavirus.',
             'Only two dogs on the Earth have ever been diagnosed with coronavirus. '
             'Moreover, even dogs who have coronavirus cannot transmit coronavirus to the human.',
             'The coronavirus vaccine is already being tested in several countries. '
             'The vaccine is going to be available this year, so a coronavirus will disappear one day.',
             'Someone who has completed quarantine or has been released from isolation '
             'does not pose a risk of coronavirus infection to other people. '
             'Can you tell me what people love doing  when people are self-isolating?']
#  NOTE!!!! YOU SHOULD CHECK THAT FACTS ARE NOT BEING CHANGED BY SENTREWRITE!
#  FORMULATE FACTS IN THIS WAY THAT THEY ARE NOT CHANGED!!! OTHERWISE THERE WILL BE BUG!!!!


def get_agephrase(age_num):
    if age_num < 20:
        phrase = 'According to the statistical data, 999 persons from 1000 in your age ' \
                 'recover after contacting coronavirus.'
    elif age_num < 40:  # prob = 0.2
        phrase = 'According to the statistical data, 499 persons from 500 ' \
                 'in your age recover after contacting coronavirus.'
    elif age_num < 50:  # prob = 0.4
        phrase = 'According to the statistical data, 249 persons from 250 ' \
                 'in your age recover after contacting coronavirus.'
    elif age_num < 60:  # prob = 1.3
        phrase = 'According to the statistical data, 76 persons from 77 ' \
                 'in your age recover after contacting coronavirus.'
    elif age_num < 70:  # prob = 3.6
        phrase = 'According to the statistical data, 27 persons from 28 ' \
                 'in your age recover after contacting coronavirus.'
    elif age_num < 80:  # prob = 8
        phrase = 'According to the statistical data, 12 persons from 13 ' \
                 'of your age recover after contacting coronavirus.'
    else:  # prob = 13.6
        phrase = 'According to the statistical data, 7 persons from 8 ' \
                 'of your age recover after contacting coronavirus.'
    phrase = phrase + ' However, it is better to stay at home as much as you can ' \
                      'to make older people safer.'
    r = random()
    if r < 0.5:
        phrase = phrase + ' While staying at home, you may use a lot of different online cinema. ' \
                          'What is the last movie you have seen?'
    else:
        phrase = phrase + ' While staying at home, you may read a lot of different books. ' \
                          'What is the last book you have ever read?'
    return phrase


def is_yes(annotated_phrase):
    return annotated_phrase['annotations']['intent_catcher'].get('yes', {}).get('detected') == 1


def is_no(annotated_phrase):
    return annotated_phrase['annotations']['intent_catcher'].get('no', {}).get('detected') == 1


def about_virus(annotated_phrase):
    return any([j in annotated_phrase['text'].lower() for j in ['virus', 'covid']])


def about_coronavirus(annotated_phrase):
    contain_words = any([j in annotated_phrase['text'] for j in ['corona', 'corana', 'corono', 'clone a',
                                                                 'colonel', 'chrono', 'quran', 'corvette',
                                                                 'current', 'kroner', 'corolla', 'crown',
                                                                 'volume', 'karuna', 'toronow', 'chrome']])
    contain_related = any([j in annotated_phrase['text'] for j in ['outbreak', 'pandemy', 'epidemy',
                                                                   'pandemi', 'epidemi']])
    return about_virus(annotated_phrase) and (contain_words or contain_related)


def get_cases_deaths(coronavirus_url):
    data = requests.get(coronavirus_url)
    num_cases = data.text.split('<strong><a href="/coronavirus/">')[1].split(' ')[0].replace(',', '')
    num_deaths = data.text.split('coronavirus/coronavirus-death-toll/"><strong>')[1].split(' ')[0].replace(',', '')
    return int(num_cases), int(num_deaths)


def wants_advice(annotated_phrase):
    request = annotated_phrase['text'].lower()
    return any([j in request for j in ['what if', 'to do', 'should i do']])


def know_symptoms(annotated_phrase):
    request = annotated_phrase['text'].lower()
    return any([j in request for j in ['symptoms', 'do i have', 'tell from', 'if i get']])


def get_state_cases(states_url):
    data = requests.get(states_url).text.lower()
    data = data.split('here are the rest of the cases, broken down by state')[1]
    state_data = dict()
    for state_name in STATES.keys():
        number = data[data.find(state_name):].split('</div>')[0]
        number = number.replace('</strong>', '').replace('<strong>', '')
        for i in range(len(number)):
            if number[i] in '0123456789':
                number = number[i:]
                break
        if ':' in number:
            number = number.split(':')[1]
        state_data[state_name] = number
    return state_data


def get_statephrase(state_name, state_data):
    data1 = [state_name, state_data[state_name], STATES[state_name]]
    phrase = 'The total number of registered coronavirus cases in {0} is {1}. ' \
             'By the way, the population of {0} is {2} persons, which is way larger than ' \
             'the number of cases. '.format(*data1)
    return phrase


def check_about_death(last_utterance):
    return any([j in last_utterance['text'] for j in ['death', 'die', 'dying', 'mortality']])


def get_age_answer(last_utterance):
    try:
        age_num = None
        user_phrase = last_utterance['text']
        for punct in punctuation:
            user_phrase = user_phrase.replace(punct, ' ')
        user_words = user_phrase.split(' ')
        for user_word in user_words:
            if user_word.isdigit():
                age_num = int(user_word)
        if age_num is None:
            age_num = word_to_num(last_utterance['text'])
        reply = get_agephrase(age_num)
    except BaseException:
        reply = "I didn't get your age. Could you, please, repeat it."
    return reply


def make_phrases(n_cases, n_deaths, num_flu_deaths, millionair_number):
    logger.info('Making data')
    n_times1 = millionair_number // n_cases
    n_times2 = num_flu_deaths // n_deaths
    nums1 = [n_cases, n_times1]
    nums2 = [n_deaths, n_times2]
    assert len(nums1) == 2
    assert len(nums2) == 2
    phrase1 = 'According to the recent data, there are  {0} confirmed cases of coronavirus. ' \
              'This is about {1} times less than the number of millionaires, ' \
              'so you are not likely to catch it any time soon. ' \
              ' Would you like to hear another fact about coronavirus?'.format(*nums1)
    phrase2 = 'According to the recent data, there are {0} confirmed deaths from coronavirus. ' \
              'This is  about {1} times less than the number of people ' \
              'died from flu last year, so you are not likely to die from it any time soon. ' \
              'After all, you have lived through the last winter somehow! '.format(*nums2)
    return [phrase1, phrase2]


def improve_phrase(phrase, asked_about_age=True, met_last=True):
    if met_last and asked_about_age:
        return phrase
    if asked_about_age:
        phrase = phrase + ' Would you like to hear another fact about coronavirus?'
    else:
        phrase = phrase + 'Anyway, I can tell you how likely you are '\
                          'to recover from coronavirus if you get it. ' \
                          'What is your age? '
    return phrase


def return_fact(facts, last_bot_phrases, asked_about_age=False, met_last=False):
    last_bot_phrases = [j.lower() for j in last_bot_phrases]
    phrase_ends = ['anyway, i can tell', 'do you want to know']
    #  logging.info('Last bot phrases before and after transition')
    #  logging.info(last_bot_phrases)
    for i in range(len(last_bot_phrases)):
        phrase = last_bot_phrases[i].lower()
        for phrase_end in phrase_ends:
            phrase = phrase.split(phrase_end)[0]
        phrase = ' '.join(phrase.strip().split(' '))
        last_bot_phrases[i] = phrase
    #  logging.info(last_bot_phrases)
    for fact in facts:
        met_before = any([fact.lower() in phrase.lower()
                          for phrase in last_bot_phrases])
        if not met_before:
            if fact != facts[-1] and not met_last:
                #  logging.info('*****')
                #  logging.info(fact)
                #  logging.info(last_bot_phrases[0])
                #  pr=False
                #  for i in range(1,min(len(fact), len(last_bot_phrases[0]))):
                #    if fact[:i] != last_bot_phrases[:i] and not pr:
                #        logging.info(fact[:i])
                #        logging.info(last_bot_phrases[:i])
                #        logging.info(i)
                #        pr=True
                fact = improve_phrase(fact, asked_about_age, met_last)
            return fact


class CoronavirusSkillScenario:

    def __init__(self):
        try:
            num_cases, num_cv_deaths = get_cases_deaths(CORONAVIRUS_URL)
            num_flu_deaths = 560000
            millionaire_number = 46800000
            self.phrases = make_phrases(num_cases, num_cv_deaths, num_flu_deaths, millionaire_number)
            self.state_cases = get_state_cases(STATES_URL)
            self.facts = [j.lower() for j in FACT_LIST]
            self.symptom_phrase = 'According to the CDC website, ' \
                                  'The main warning signs of coronavirus are: ' \
                                  'difficulty breathing or shortness of breath, ' \
                                  'persistent pain or pressure in the chest , ' \
                                  'new confusion or inability to arouse, ' \
                                  'bluish lips or face. If you develop any of these signs,' \
                                  'get a medical attention. '
            self.advice_phrase = 'According to the CDC website, ' \
                                 'To protect yourself and others from the coronavirus, ' \
                                 'you should do the following: ' \
                                 'clean your hands often, ' \
                                 'avoid close contact with people, especially elderly ones, ' \
                                 'clean and disinfect frequently touched surfaces, '\
                                 'cover your coughs and sneeses.' \
                                 'If you are sick, wear a face mask and try to stay at home as much as possible.'
        except Exception as e:
            logger.exception('Exception while retrieving new info about coronavirus')
            sentry_sdk.capture_exception(e)

    def __call__(self, dialogs):
        texts = []
        confidences = []
        for dialog in dialogs:
            try:
                confidence = 0
                if len(dialog['utterances']) >= 2:
                    last_bot_phrase = dialog['utterances'][-2]['text'].lower()
                else:
                    last_bot_phrase = ''
                last_utterance = dialog['utterances'][-1]
                last_utterances = []
                #  logging.info('*#*')
                #  logging.info([j['text'] for j in dialog['utterances']])
                min_back_len = len(dialog['utterances'])
                #  logging.info(min_back_len)
                for i in range(1, min_back_len, 2):
                    if len(dialog['utterances']) >= i:
                        last_utterances.append(dialog['utterances'][-i]['text'].lower())
                last_bot_phrases = []
                for i in range(2, min_back_len, 2):
                    if len(dialog['utterances']) >= i:
                        last_bot_phrases.append(dialog['utterances'][-i]['text'].lower())
                last_bot_phrase = ''
                if len(last_bot_phrases) > 0:
                    last_bot_phrase = last_bot_phrases[0]
                met_last = any([self.facts[-1].lower() in j.lower() for j in last_bot_phrases])
                logging.info(last_bot_phrases)
                logging.info(met_last)
                asked_about_age = any(['what is your age' in j for j in last_bot_phrases])
                #  logging.info(asked_about_age)
                if 'would you like to hear another fact' in last_bot_phrase and is_no(last_utterance):
                    reply, confidence = '', 0
                elif know_symptoms(last_utterance) and about_coronavirus(last_utterance):
                    reply, confidence = self.symptom_phrase, 1
                    reply = improve_phrase(reply, asked_about_age, met_last)
                elif wants_advice(last_utterance) and about_coronavirus(last_utterance):
                    reply, confidence = self.advice_phrase, 1
                    reply = improve_phrase(reply, asked_about_age, met_last)
                elif any([j in last_bot_phrase for j in (['do you want to know another fact'] + FACT_LIST)]):
                    logging.info('!*!!')
                    logging.info(last_utterance)
                    logging.info(is_yes(last_utterance))
                    if is_yes(last_utterance):
                        reply, confidence = return_fact(self.facts, last_bot_phrases,
                                                        asked_about_age, met_last), 1
                        if reply is None:
                            reply, confidence = '', 0
                    else:
                        reply, confidence = '', 0

                else:
                    detected_state = None
                    for utterance in last_utterances:
                        for state_name in STATES.keys():
                            if state_name in utterance and detected_state is None:
                                detected_state = state_name
                    if detected_state is None:  # No state dialog
                        if about_virus(last_utterance) and not about_coronavirus(last_utterance):
                            reply, confidence = 'I suppose you are asking about coronavirus. Is it right?', 1
                        else:
                            wants_cv = is_yes(last_utterance) and 'you are asking about coronavirus' in last_bot_phrase
                            #  logging.info(last_bot_phrases)
                            not_seen_before = all(['confirmed cases of' not in j for j in last_bot_phrases])
                            #  logging.info(not_seen_before)
                            was_firstphrase = is_yes(last_utterance) and 'the number of millionaires' in last_bot_phrase
                            about_death = check_about_death(last_utterance)
                            if 'is your age' in last_bot_phrase or "didn't get your age" in last_bot_phrase:
                                reply, confidence = get_age_answer(last_utterance), 1
                            elif was_firstphrase or about_death:
                                reply, confidence = self.phrases[1], 1.0
                                reply = improve_phrase(reply, asked_about_age, met_last)
                            elif (wants_cv or about_coronavirus(last_utterance)) and not_seen_before:
                                reply, confidence = self.phrases[0], 1
                                # DOESNT' NEED IMPROVEMENT
                            else:
                                logging.info('!*!!')
                                logging.info(last_utterance)
                                logging.info(is_yes(last_utterance))
                                if is_yes(last_utterance):
                                    reply, confidence = return_fact(self.facts, last_bot_phrases,
                                                                    asked_about_age, met_last), 1
                                    if reply is None:
                                        reply, confidence = '', 0
                                else:
                                    reply, confidence = '', 0
                    else:  # Detected some state
                        if about_virus(last_utterance) and not about_coronavirus(last_utterance):
                            reply = 'I suppose you are asking about ' \
                                    'coronavirus in {0}. Is it right?'.format(detected_state)
                            confidence = 0.99
                        else:
                            wants_cv = all([is_yes(last_utterance),
                                           'you are asking about coronavirus in' in last_bot_phrase])
                            wasnot_first = 'of registered coronavirus' not in last_bot_phrase
                            if 'is your age' in last_bot_phrase or "didn't get your age" in last_bot_phrase:
                                reply, confidence = get_age_answer(last_utterance), 1
                            elif (wants_cv or about_coronavirus(last_utterance)) and wasnot_first:
                                reply, confidence = get_statephrase(detected_state, self.state_cases), 1
                                reply = improve_phrase(reply, asked_about_age, met_last)
                            else:
                                logging.info('!*!!')
                                logging.info(last_utterance)
                                logging.info(is_yes(last_utterance))
                                if is_yes(last_utterance):
                                    reply, confidence = return_fact(self.facts, last_bot_phrases,
                                                                    asked_about_age, met_last), 1
                                    if reply is None:
                                        reply, confidence = '', 0
                                else:
                                    reply, confidence = '', 0
                if reply.lower() == last_utterance['text'].lower():
                    confidence = 0
                elif reply.lower() in last_utterances and confidence == 1:
                    confidence = 0.95

            except Exception as e:
                logger.exception("exception in coronavirus skill")
                sentry_sdk.capture_exception(e)
                reply = ""
                confidence = 0
            texts.append(reply)
            confidences.append(confidence)

        return texts, confidences  # , human_attributes, bot_attributes, attributes
