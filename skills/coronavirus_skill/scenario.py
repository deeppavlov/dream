import logging
from os import getenv
import sentry_sdk
import requests
from string import punctuation
from word2number.w2n import word_to_num
from random import random
import json
import pandas as pd
from copy import deepcopy
import threading
import time
from datetime import datetime, timedelta
from collections import defaultdict
from common.utils import is_yes, is_no, corona_switch_skill_reply
from common.utils import check_about_death, about_virus, quarantine_end
sentry_sdk.init(getenv('SENTRY_DSN'))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)
CORONAVIRUS_URL = 'https://www.worldometers.info/coronavirus/coronavirus-cases/'
STATES = {j.strip().lower().split(';')[0]: j.strip().lower().split(';')[1]
          for j in open('state_names.txt', 'r').readlines()}
#  NYT_API_KEY = '1cc135af-30ab-4f9f-9bb6-76a457036152'
#  counties_url = 'https://www.nytimes.com/interactive/2020/us/coronavirus-us-cases.html?api-key=' + NYT_API_KEY
#  os.chdir('C://Users//DK//Documents//DATA')
DATA_URL = 'http://raw.githubusercontent.com/CSSEGISandData/COVID-19/' \
           'master/csse_covid_19_data/csse_covid_19_daily_reports/'
COUNTIES = json.load(open('county_city.json', 'r'))
for key in deepcopy(list(COUNTIES.keys())):
    key1 = tuple(key.lower().split('_'))
    COUNTIES[key1] = COUNTIES[key]
    del COUNTIES[key]
CITIES = defaultdict(list)
for county_name in COUNTIES:
    for city_name in COUNTIES[county_name][1:]:
        CITIES[city_name.lower()].append((county_name, COUNTIES[county_name][0]))
STATE_DATA, COUNTY_DATA = None, None
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
QUARANTINE_END_PHRASE = 'In the United States of America, the full quarantine is expected to last ' \
                        'at least until the Easter. After that, we will decide what to do next.'
ORIGIN_PHRASE = 'According to the scientific data, coronavirus COVID 19 is a product of natural evolution. ' \
                'The first place where it caused an outbreak is the city of Wuhan, China.'
WHAT_PHRASE = 'Coronavirus COVID 19 is an infectious disease. ' \
              'Its common symptoms include fever, cough, and shortness of breath. ' \
              'While the majority of cases result in mild symptoms, some cases can be lethal.'

for city_name in CITIES.keys():
    val_, i_ = 0, 0
    for i, value in enumerate(CITIES[city_name]):
        if value[1] > val_:
            val_, i_ = value[1], i
    CITIES[city_name] = CITIES[city_name][i_]


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


def about_coronavirus(annotated_phrase):
    contain_words = any([j in annotated_phrase['text'] for j in ['corona', 'corana', 'corono', 'clone a',
                                                                 'colonel', 'chrono', 'quran', 'corvette',
                                                                 'current', 'kroner', 'corolla', 'crown',
                                                                 'volume', 'karuna', 'toronow', 'chrome',
                                                                 'code nineteen']])
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


def get_state_cases(data_url=DATA_URL):
    global STATE_DATA, COUNTY_DATA
    while True:
        current_date = datetime.now().strftime('%m-%d-%Y') + '.csv'
        prev_date = (datetime.now() - timedelta(days=1)).strftime('%m-%d-%Y') + '.csv'
        try:
            current_data = pd.read_csv((data_url + current_date), error_bad_lines=False)
        except BaseException:
            current_data = pd.read_csv((data_url + prev_date), error_bad_lines=False)
        current_data = current_data[current_data['Country_Region'] == 'US']
        state_data = defaultdict(lambda: (0, 0))
        county_data = defaultdict(lambda: (0, 0))  # (state, county)
        for i in current_data.index:
            state = current_data['Province_State'][i].lower()
            deaths = current_data['Deaths'][i]
            cases = current_data['Confirmed'][i]
            state_tuple = (state_data[state][0] + cases, state_data[state][1] + deaths)
            state_data[state] = state_tuple
            try:
                county = current_data['Admin2'][i].lower() + ' county'
                county_data[(county, state)] = (cases, deaths)
            except BaseException:
                pass
        STATE_DATA, COUNTY_DATA = state_data, county_data
        time.sleep(60 * 60 * 12)


def get_statephrase(state_name, state_data, county_data):
    # state_data, county_data = get_state_cases(STATES_URL, COUNTIES_URL)
    # state_name = 'houston'
    if type(state_name) == str:
        state_name = state_name.lower()
    logging.info(state_name)
    county_names = [j[0] for j in COUNTIES.keys()]
    if state_name in STATES.keys():
        data1 = [state_name, state_data[state_name][0], state_data[state_name][1], STATES[state_name]]
        phrase = 'The total number of registered coronavirus cases in {0} is {1} including {2} deaths. ' \
                 'By the way, the population of {0} is {3} persons, which is way larger than ' \
                 'the number of cases. '.format(*data1)
    elif state_name in CITIES.keys():
        county_name = CITIES[state_name][0]
        data1 = [state_name,
                 ','.join([j for j in county_name]),
                 county_data[county_name][0],
                 county_data[county_name][1],
                 COUNTIES[county_name][0]]
        phrase = '{0} is located in {1}. ' \
                 'In this county, the total number of registered coronavirus cases ' \
                 'is {2} including {3} deaths. ' \
                 'By the way, the population of this county is {4} persons, ' \
                 'which is way larger than ' \
                 'the number of cases'.format(*data1)
    elif state_name in county_names:
        data1 = [','.join([j for j in state_name]),
                 county_data[state_name][0],
                 county_data[state_name][1],
                 COUNTIES[state_name][0]]
        phrase = 'In the {0}, the total number of registered coronavirus cases ' \
                 'is {1} including {2} deaths.' \
                 'By the way, the population of this county is {3} persons, ' \
                 'which is way larger than ' \
                 'the number of cases'.format(*data1)
    else:
        raise Exception(str(state_name) + ' not in names')
    if data1[2] == 1:
        phrase = phrase.replace('deaths', 'death')
    elif data1[2] == 0:
        phrase = phrase.replace('0 deaths', 'no deaths')
    return phrase


def get_age_answer(last_utterance):
    try:
        age_num = None
        user_phrase = last_utterance['text']
        logging.debug('Age answer for ')
        logging.debug(user_phrase)
        for punct in punctuation:
            user_phrase = user_phrase.replace(punct, ' ')
        user_words = user_phrase.split(' ')
        for user_word in user_words:
            if user_word.isdigit():
                age_num = int(user_word)
        if age_num is None:
            age_num = word_to_num(user_phrase)
        reply = get_agephrase(age_num)
    except BaseException:
        reply = "I didn't get your age. Could you, please, repeat it."
    logging.debug(reply)
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
              ' Would you like to learn more about coronavirus?'.format(*nums1)
    phrase2 = 'According to the recent data, there are {0} confirmed deaths from coronavirus. ' \
              'This is  about {1} times less than the number of people ' \
              'died from flu last year, so you are not likely to die from it any time soon. ' \
              'After all, you have lived through the last winter somehow! '.format(*nums2)
    return [phrase1, phrase2]


def improve_phrase(phrase, asked_about_age=True, met_last=True):
    if met_last and asked_about_age:
        return phrase
    if asked_about_age:
        phrase = phrase + ' Would you like to learn more about coronavirus?'
    else:
        phrase = phrase + ' Anyway, I can tell you how likely you are ' \
                          'to recover from coronavirus if you get it. ' \
                          'What is your age? '
    return phrase


def asked_origin(last_utterance):
    return any([j in last_utterance['text'].lower() for j in ['origin', 'come from']])


def asked_whatvirus(last_utterance):
    return any([j in last_utterance['text'].lower() for j in ['what is corona', "what's corona"]])


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
            self._updating_thread = threading.Thread(target=get_state_cases)
            self._updating_thread.start()
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
                                 'clean and disinfect frequently touched surfaces, ' \
                                 'cover your coughs and sneeses.' \
                                 'If you are sick, wear a face mask and try to stay at home as much as possible.'
        except Exception as e:
            logger.exception('Exception while retrieving new info about coronavirus')
            sentry_sdk.capture_exception(e)

    def __call__(self, dialogs):
        global STATE_DATA, COUNTY_DATA
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
                if quarantine_end(last_utterance):
                    logging.info('Quarantine end detected')
                    reply, confidence = QUARANTINE_END_PHRASE, 0.95
                elif 'would you like to learn more' in last_bot_phrase:
                    fear_prob = dialog['utterances'][-1]['annotations']['emotion_classification']['text']['fear']
                    logging.debug('Fear prob ' + str(fear_prob))
                    if is_no(last_utterance):
                        logging.info('Another fact request detected, answer is NO')
                        reply = corona_switch_skill_reply()
                        confidence = 0.98
                    elif fear_prob > 0.9:
                        logging.info('Corona fear detected')
                        reply = 'Just stay home, wash your hands and you will be fine. We will get over it.'
                        confidence = 0.95
                    elif is_yes(last_utterance):
                        logging.info('Returning a fact')
                        reply, confidence = return_fact(self.facts, last_bot_phrases,
                                                        asked_about_age, met_last), 1
                    else:
                        reply, confidence = '', 0
                elif know_symptoms(last_utterance) and about_coronavirus(last_utterance):
                    logging.info('Symptom request detected')
                    reply, confidence = self.symptom_phrase, 1
                    reply = improve_phrase(reply, asked_about_age, met_last)
                elif wants_advice(last_utterance) and about_coronavirus(last_utterance):
                    logging.info('Advice request detected')
                    reply, confidence = self.advice_phrase, 1
                    reply = improve_phrase(reply, asked_about_age, met_last)
                elif any([j in last_bot_phrase for j in (['do you want to learn more'] + FACT_LIST)]):
                    logging.info('Bot offered another fact in previous utterance')
                    if is_yes(last_utterance):
                        logging.info('Answer is YES')
                        reply, confidence = return_fact(self.facts, last_bot_phrases,
                                                        asked_about_age, met_last), 1
                        logging.info('No fact returned')
                        if reply is None:
                            reply, confidence = '', 0
                    else:
                        logging.info('Answer is not YES')
                        reply, confidence = '', 0

                else:
                    detected_state = None
                    total_names = list(STATES.keys()) + [j[0].lower() for j in COUNTIES.keys()] + list(CITIES.keys())
                    if 'suppose you are asking about' in last_bot_phrase and is_yes(last_utterance):
                        logging.info('Detecting state by 1st&2nd utt')
                        tolook_utterances = last_utterances
                    else:  # Looking only on the first utterance
                        logging.info('Detecting state by 1st utt')
                        tolook_utterances = last_utterances[:1]
                    for utterance in tolook_utterances:
                        utt1 = utterance
                        for punct in punctuation:
                            utt1 = utt1.replace(punct, ' ')
                            utt1 = ' ' + utt1 + ' '
                        for state_name in total_names:
                            name1 = ' ' + state_name + ' '
                            if name1 in utt1 and detected_state is None:
                                detected_state = state_name
                    logging.info('Detected state')
                    logging.info(detected_state)
                    logging.debug('Utterances')
                    logging.debug(tolook_utterances)
                    repeat_in_reply = False
                    if detected_state is None:  # No state dialog
                        if about_virus(last_utterance) and not about_coronavirus(last_utterance):
                            logging.info('About virus, not coronavirus')
                            reply, confidence = 'I suppose you are asking about coronavirus. Is it right?', 1
                        else:
                            wants_cv = is_yes(last_utterance) and 'you are asking about coronavirus' in last_bot_phrase
                            #  logging.info(last_bot_phrases)
                            not_seen_before = all(['confirmed cases of' not in j for j in last_bot_phrases])
                            #  logging.info(not_seen_before)
                            was_firstphrase = is_yes(last_utterance) and 'the number of millionaires' in last_bot_phrase
                            about_death = check_about_death(last_utterance)
                            is_age = False
                            if 'is your age' in last_bot_phrase or "didn't get your age" in last_bot_phrase:
                                logging.info('I have just asked about age, returning age phrase')
                                reply, confidence = get_age_answer(last_utterance), 1
                                if 'repeat it' in reply:
                                    logging.info('Could not detect age. Looking for something else')
                                    repeat_in_reply = True
                                else:
                                    is_age = True
                            if not is_age:
                                if was_firstphrase or about_death or repeat_in_reply:
                                    logging.info('I was asked about death or I offered second core fact')
                                    reply, confidence = self.phrases[1], 1.0
                                    reply = improve_phrase(reply, asked_about_age, met_last)
                                elif (wants_cv or about_coronavirus(last_utterance)) and not_seen_before:
                                    logging.info('Returning first phrase')
                                    reply, confidence = self.phrases[0], 1
                                    # DOESNT' NEED IMPROVEMENT
                                else:
                                    if is_yes(last_utterance):
                                        logging.info('YES received - returning fact')
                                        reply, confidence = return_fact(self.facts, last_bot_phrases,
                                                                        asked_about_age, met_last), 1
                                        if reply is None:
                                            logging.debug('No reply received')
                                            reply, confidence = '', 0
                                    elif asked_origin(last_utterance) and about_coronavirus(last_utterance):
                                        logging.info('Origin phrase')
                                        reply, confidence = ORIGIN_PHRASE, 0.98
                                    elif asked_whatvirus(last_utterance):
                                        logging.info('What phrase')
                                        reply, confidence = WHAT_PHRASE, 0.98
                                        reply = improve_phrase(reply, asked_about_age, met_last)
                                    else:
                                        reply, confidence = '', 0
                    else:  # Detected some state
                        if about_virus(last_utterance) and not about_coronavirus(last_utterance):
                            logging.info('Detected some state, received question about virus')
                            reply = 'I suppose you are asking about ' \
                                    'coronavirus in {0}. Is it right?'.format(detected_state)
                            confidence = 0.99
                        else:
                            wants_cv = all([is_yes(last_utterance),
                                            'you are asking about coronavirus in' in last_bot_phrase])
                            wasnot_first = 'of registered coronavirus' not in last_bot_phrase
                            if 'is your age' in last_bot_phrase or "didn't get your age" in last_bot_phrase:
                                logging.info('After asking about age returning age phrase')
                                reply, confidence = get_age_answer(last_utterance), 1
                                if 'repeat it' in reply:
                                    confidence = 0
                            elif (wants_cv or about_coronavirus(last_utterance)) and wasnot_first:
                                logging.info('Returning state phrase')
                                reply, confidence = get_statephrase(detected_state, STATE_DATA,
                                                                    COUNTY_DATA), 1
                                reply = improve_phrase(reply, asked_about_age, met_last)
                            else:
                                if is_yes(last_utterance):
                                    logging.info('YES detected - returning fact')
                                    reply, confidence = return_fact(self.facts, last_bot_phrases,
                                                                    asked_about_age, met_last), 1
                                    if reply is None:
                                        logging.info('NO detected - returning zero')
                                        reply, confidence = '', 0
                                else:
                                    logging.debug('Final point')
                                    reply, confidence = '', 0
                if reply.lower() == last_utterance['text'].lower():
                    logging.info('Not to selfrepeat, drop confidence to 0')
                    confidence = 0
                elif reply.lower() in last_utterances and confidence == 1:
                    logging.debug('I have said that before, a bit less confident')
                    confidence = 0.95

            except Exception as e:
                logger.exception("exception in coronavirus skill")
                sentry_sdk.capture_exception(e)
                reply = ""
                confidence = 0
            texts.append(reply)
            confidences.append(confidence)

        return texts, confidences  # , human_attributes, bot_attributes, attributes
