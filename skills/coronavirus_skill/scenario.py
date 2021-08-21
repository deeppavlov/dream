import json
import logging
import re
import threading
import time
from datetime import datetime, timedelta
from collections import defaultdict
from copy import deepcopy
from os import getenv
from random import random
from string import punctuation

import pandas as pd
import sentry_sdk
from word2number.w2n import word_to_num

from common.coronavirus import (
    CORONA_SWITCH_BEGIN,
    corona_switch_skill_reply,
    is_staying_home_requested,
    check_about_death,
    about_virus,
    quarantine_end,
    vaccine_safety_request,
)
from common.link import link_to
from common.utils import is_yes, is_no, get_emotions
from common.universal_templates import book_movie_music_found, if_chat_about_particular_topic, is_switch_topic


sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)
CORONAVIRUS_URL = (
    "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/" "csse_covid_19_data/csse_covid_19_time_series"
)
DEATH_URL = f"{CORONAVIRUS_URL}/time_series_covid19_deaths_global.csv"
CASE_URL = f"{CORONAVIRUS_URL}/time_series_covid19_confirmed_global.csv"
STATES = {
    j.strip().lower().split(";")[0]: j.strip().lower().split(";")[1] for j in open("state_names.txt", "r").readlines()
}
NATIONS = {
    j.strip().lower().split(";")[0]: j.strip().lower().split(";")[1] for j in open("nation_names.txt", "r").readlines()
}
#  NYT_API_KEY = '1cc135af-30ab-4f9f-9bb6-76a457036152'
#  counties_url = 'https://www.nytimes.com/interactive/2020/us/coronavirus-us-cases.html?api-key=' + NYT_API_KEY
#  os.chdir('C://Users//DK//Documents//DATA')
DATA_URL = (
    "http://raw.githubusercontent.com/CSSEGISandData/COVID-19/" "master/csse_covid_19_data/csse_covid_19_daily_reports/"
)
COUNTIES = json.load(open("county_city.json", "r"))
for key in deepcopy(list(COUNTIES.keys())):
    key1 = tuple(key.lower().split("_"))
    COUNTIES[key1] = COUNTIES[key]
    del COUNTIES[key]
CITIES = defaultdict(list)
for county_name in COUNTIES:
    for city_name in COUNTIES[county_name][1:]:
        CITIES[city_name.lower()].append((county_name, COUNTIES[county_name][0]))
STATE_DATA, COUNTY_DATA, NATION_DATA = None, None, None
FACT_LIST = [
    "Only two dogs and two cats on the Earth have ever been diagnosed with coronavirus. "
    "Moreover, even dogs and cats who have coronavirus cannot transmit coronavirus to the human.",
    "Wearing face masks reduces your infection chance by 65%.",
    "Someone who has completed quarantine or has been released from isolation "
    "does not pose a risk of coronavirus infection to other people. "
    "Can you tell me what people love doing  when people are self-isolating?",
]
#  NOTE!!!! YOU SHOULD CHECK THAT FACTS ARE NOT BEING CHANGED BY SENTREWRITE!
#  FORMULATE FACTS IN THIS WAY THAT THEY ARE NOT CHANGED!!! OTHERWISE THERE WILL BE BUG!!!!
VACCINE_SAFETY_PHRASE = (
    "All CDC-approved vaccines are safe enough for you - "
    "of course, if your doctor does not mind against using them."
    "I can't say the same about getting infected, however, "
    "so vaccines are necessary to prevent people from that.."
)

QUARANTINE_END_PHRASE = (
    "Although most American states are easing the restrictions, "
    "the Coronavirus pandemics in the majority of the states hasn't been reached yet. "
    "If you want to help ending it faster, please continue social distancing as much as you can. "
)
ORIGIN_PHRASE = (
    "According to the scientific data, coronavirus COVID 19 is a product of natural evolution. "
    "The first place where it caused an outbreak is the city of Wuhan, China."
)
WHAT_PHRASE = (
    "Coronavirus COVID 19 is an infectious disease. "
    "Its common symptoms include fever, cough, shortness of breath, and many others."
    "Anyone can have mild to severe symptoms. While the majority of cases result in mild symptoms,"
    "some cases can be lethal. Older adults and people who have severe underlying medical conditions"
    "like heart or lung disease or diabetes seem to be at higher risk for developing more serious"
    "complications from COVID-19 illness."
)
WORK_AND_STAY_HOME_PHRASE = (
    "Every day that you practice social distancing during the pandemic, "
    "you are doing someone else (maybe hundreds or even thousands of someone elses) "
    "a great kindness. "
    "So if you can, stay home, and vaccinate it you have not already done it."
    "It's the easiest act of heroism you'll ever do. "
    "Would you like to learn more about coronavirus?"
)
CDC_STAY_HOME_RECOMMENDATION = (
    "While some of the communities and businesses are re-opening, CDC recommends Americans"
    "to understand potential risks and use different measures to maximize their own safety."
    "If you are not vaccinated yet, please wear masks, practice social distancing,"
    "and minimize time you have to spend outside of your home."
)
EXPLAIN_PHRASE = (
    "If you are outside your home, you can get a coronavirus. "
    "Even if you easily overcome it, you can begin a chain of many new infections, "
    "which can be critical or deadly for some."
    "So unless you work in healthcare or other essential industries,"
    "social distancing is your best bet."
)
FEAR_HATE_REPLY1 = (
    "Please, calm down. We are a strong nation, we are vaccinating people " "and we will overcome this disease one day."
)
FEAR_HATE_REPLY2 = (
    "Please, chin up. We have already defeated a hell lot of diseases, "
    "and I am sure that coronavirus will be the next one."
)
CURE_REPLY = (
    "There is no cure designed for COVID-19 yet. "
    "You can consult with CDC.gov website for detailed information about the ongoing work on the cure."
)
BOT_CORONAVIRUS_PHRASE = "As a socialbot, I don't have coronavirus. I hope you won't have it either."
for city_name in CITIES.keys():
    val_, i_ = 0, 0
    for i, value in enumerate(CITIES[city_name]):
        if value[1] > val_:
            val_, i_ = value[1], i
    CITIES[city_name] = CITIES[city_name][i_]


def get_agephrase(age_num, bot_attr, human_attr):
    if age_num < 20:
        phrase = (
            "According to the statistical data, 999 persons from 1000 in your age "
            "recover after contacting coronavirus."
        )
    elif age_num < 40:  # prob = 0.2
        phrase = (
            "According to the statistical data, 499 persons from 500 "
            "in your age recover after contacting coronavirus."
        )
    elif age_num < 50:  # prob = 0.4
        phrase = (
            "According to the statistical data, 249 persons from 250 "
            "in your age recover after contacting coronavirus."
        )
    elif age_num < 60:  # prob = 1.3
        phrase = (
            "According to the statistical data, 76 persons from 77 " "in your age recover after contacting coronavirus."
        )
    elif age_num < 70:  # prob = 3.6
        phrase = (
            "According to the statistical data, 27 persons from 28 " "in your age recover after contacting coronavirus."
        )
    elif age_num < 80:  # prob = 8
        phrase = (
            "According to the statistical data, 12 persons from 13 " "of your age recover after contacting coronavirus."
        )
    else:  # prob = 13.6
        phrase = (
            "According to the statistical data, 7 persons from 8 " "of your age recover after contacting coronavirus."
        )
    phrase = f"{phrase} However, it is better to stay at home as much as you can " "to make older people safer."
    r = random()
    if r < 0.5:
        phrase = f"{phrase} While staying at home, you may use a lot of different online cinema. "
        link = link_to(["dff_movie_skill"], human_attributes=human_attr)
        human_attr["used_links"][link["skill"]] = human_attr["used_links"].get(link["skill"], []) + [link["phrase"]]
        phrase = f"{phrase} {link['phrase']}"
    else:
        phrase = f"{phrase} While staying at home, you may read a lot of different books. "
        link = link_to(["book_skill"], human_attributes=human_attr)
        human_attr["used_links"][link["skill"]] = human_attr["used_links"].get(link["skill"], []) + [link["phrase"]]
        phrase = phrase + link["phrase"]
    return phrase, bot_attr, human_attr


pandemy_request = re.compile(r"(outbreak|pandemy|epidemy|pandemi|epidemi)", re.IGNORECASE)
corona_request = re.compile(
    r"(corona|corana|corono|clone a|colonel|chrono|quran|corvette|current|kroner|corolla|"
    r"crown|volume|karuna|toronow|chrome|code nineteen|covid)",
    re.IGNORECASE,
)


def about_coronavirus(annotated_phrase):
    if re.search(corona_request, annotated_phrase["text"]):
        contain_words = True
    else:
        contain_words = False
    if re.search(pandemy_request, annotated_phrase["text"]):
        contain_related = True
    else:
        contain_related = False
    return about_virus(annotated_phrase) and (contain_words or contain_related)


chances_request = re.compile(r"(what are my chances|will i die)", re.IGNORECASE)


def get_chance_request(last_utterance):
    if isinstance(last_utterance, str):
        last_utterance = {"text": last_utterance}
    if re.search(chances_request, last_utterance["text"]):
        return True
    return False


def get_cases_deaths():
    case_data = pd.read_csv(CASE_URL, error_bad_lines=False)
    death_data = pd.read_csv(DEATH_URL, error_bad_lines=False)
    num_cases = case_data[case_data.columns[-1]].sum()
    num_deaths = death_data[death_data.columns[-1]].sum()
    return int(num_cases), int(num_deaths)


advice_request = re.compile(r"(what if|to do| should i do)", re.IGNORECASE)


def wants_advice(annotated_phrase):
    if re.search(advice_request, annotated_phrase["text"]):
        return True
    return False


symptoms_request = re.compile(r"(symptoms|do i have|tell from|if i get)", re.IGNORECASE)


def know_symptoms(annotated_phrase):
    if re.search(symptoms_request, annotated_phrase["text"]):
        return True
    return False


def get_state_cases():
    global STATE_DATA, COUNTY_DATA, NATION_DATA
    while True:
        current_date = datetime.now().strftime("%m-%d-%Y") + ".csv"
        prev_date = (datetime.now() - timedelta(days=1)).strftime("%m-%d-%Y") + ".csv"
        prev_prev_date = (datetime.now() - timedelta(days=2)).strftime("%m-%d-%Y") + ".csv"
        current_data = None
        for date_ in [prev_prev_date, prev_date, current_date]:
            try:
                current_data = pd.read_csv((DATA_URL + date_), error_bad_lines=False)
                logging.info(f"Data for  {date_} retrieved")
            except BaseException:
                pass
        if current_data is None:
            raise Exception("Data not retrieved")
        current_data = current_data[current_data["Country_Region"] == "US"]
        state_data = defaultdict(lambda: (0, 0))
        county_data = defaultdict(lambda: (0, 0))  # (state, county)
        nation_data = defaultdict(lambda: (0, 0))  # cases, deaths
        for i in current_data.index:
            state = current_data["Province_State"][i].lower()
            deaths = current_data["Deaths"][i]
            cases = current_data["Confirmed"][i]
            state_tuple = (state_data[state][0] + cases, state_data[state][1] + deaths)
            state_data[state] = state_tuple
            try:
                county = current_data["Admin2"][i].lower() + " county"
                county_data[(county, state)] = (cases, deaths)
            except BaseException:
                pass
        case_data = pd.read_csv(CASE_URL, error_bad_lines=False)
        death_data = pd.read_csv(DEATH_URL, error_bad_lines=False)
        case_data = case_data.groupby("Country/Region").sum()
        death_data = death_data.groupby("Country/Region").sum()
        for nation_name in case_data.index:
            case_num = case_data[case_data.columns[-1]][nation_name]
            death_num = death_data[death_data.columns[-1]][nation_name]
            nation_data[nation_name.lower()] = case_num, death_num
        STATE_DATA, COUNTY_DATA, NATION_DATA = state_data, county_data, nation_data
        time.sleep(60 * 60 * 12)


def get_statephrase(state_name, state_data, county_data, nation_data):
    # state_data, county_data = get_state_cases(STATES_URL, COUNTIES_URL)
    # state_name = 'houston'
    if type(state_name) == str:
        state_name = state_name.lower()
    logging.info(state_name)
    county_names = [j[0] for j in COUNTIES.keys()]
    if state_name in STATES.keys():
        data1 = [state_name, state_data[state_name][0], state_data[state_name][1], STATES[state_name]]
        phrase = "The total number of registered coronavirus cases in {0} is {1} including {2} deaths.".format(*data1)
    elif state_name in nation_data.keys():
        data1 = [state_name, nation_data[state_name][0], nation_data[state_name][1], NATIONS[state_name]]
        phrase = "The total number of registered coronavirus cases in {0} is {1} including {2} deaths.".format(*data1)
    elif state_name in CITIES.keys():
        county_name = CITIES[state_name][0]
        data1 = [
            state_name,
            ",".join([j for j in county_name]),
            county_data[county_name][0],
            county_data[county_name][1],
            COUNTIES[county_name][0],
        ]
        phrase = (
            "{0} is located in {1}. "
            "In this county, the total number of registered coronavirus cases "
            "is {2} including {3} deaths.".format(*data1)
        )
    elif state_name in county_names:
        for county in COUNTIES.keys():
            if county[0] == state_name:
                state_name = county
        data1 = [
            ",".join([j for j in state_name]),
            county_data[state_name][0],
            county_data[state_name][1],
            COUNTIES[state_name][0],
        ]
        phrase = "In the {0}, the total number of registered coronavirus cases " "is {1} including {2} deaths.".format(
            *data1
        )
    else:
        raise Exception(f"{state_name} not in names")
    if data1[2] == 1:
        phrase = phrase.replace("deaths", "death")
    elif data1[2] == 0:
        phrase = phrase.replace("0 deaths", "no deaths")
    return phrase


def get_age_answer(last_utterance, bot_attr, human_attr):
    try:
        age_num = None
        user_phrase = last_utterance["text"]
        logging.debug("Age answer for ")
        logging.debug(user_phrase)
        for punct in punctuation:
            user_phrase = user_phrase.replace(punct, " ")
        user_words = user_phrase.split(" ")
        for user_word in user_words:
            if user_word.isdigit():
                age_num = int(user_word)
        if age_num is None:
            age_num = word_to_num(user_phrase)
        reply, bot_attr, human_attr = get_agephrase(age_num, bot_attr, human_attr)
    except BaseException:
        reply = ""
    logging.debug(reply)
    return reply, bot_attr, human_attr


def make_phrases(n_cases, n_deaths, num_flu_deaths, millionair_number):
    logger.info("Making data")
    n_times1 = millionair_number // n_cases
    n_times2 = num_flu_deaths // n_deaths
    nums1 = [n_cases, n_times1]
    nums2 = [n_deaths, n_times2]
    assert len(nums1) == 2
    assert len(nums2) == 2
    phrase1 = (
        "According to the recent data, there are  {0} confirmed cases of coronavirus. "
        " Shall I tell you more?".format(*nums1)
    )
    phrase2 = "According to the recent data, there are {0} confirmed deaths from coronavirus.".format(*nums2)
    return [phrase1, phrase2]


def emotion_detected(annotated_phrase, name="fear"):
    threshold = 0.8
    emotion_probs = get_emotions(annotated_phrase, probs=True)
    return emotion_probs.get(name, 0) > threshold


def improve_phrase(phrase, asked_about_age=True, met_last=True):
    if met_last and asked_about_age:
        return phrase
    if asked_about_age:
        phrase = phrase + " Would you want to learn more?"
    else:
        phrase = (
            phrase + " Anyway, I can approximately tell you how likely you are "
            "to recover from coronavirus if you get it. "
            "What is your age? "
        )
    return phrase


origin_request = re.compile(r"(origin|come from|where did it start)", re.IGNORECASE)


def asked_origin(last_utterance):
    if re.search(origin_request, last_utterance["text"]):
        return True
    return False


dontlike_request = re.compile(
    r"(don't like|don't want to talk|don't want to hear|not concerned about|"
    r"over the coronavirus|no coronavirus|stop talking about|no more coronavirus|"
    r"don't want to listen)",
    re.IGNORECASE,
)


def dontlike(last_utterance):
    last_uttr_text = last_utterance["text"].lower()
    last_uttr_text = last_uttr_text.replace("wanna", "want to")
    if re.search(dontlike_request, last_uttr_text):
        return True
    return False


vaccine_request = re.compile(r"(cure|treatment|vaccine)", re.IGNORECASE)


def asked_cure(last_utterance):
    if re.search(vaccine_request, last_utterance["text"]):
        return True
    return False


corona_definition_request = re.compile(r"(what is corona|what's corona|what is the pandemic)", re.IGNORECASE)


def asked_whatvirus(last_utterance):
    if re.search(corona_definition_request, last_utterance["text"]):
        return True
    return False


doyouhave_request = re.compile(
    r"(do you have|have you got|are you getting|have you ever got|are you sick with|" r"have you come down with)",
    re.IGNORECASE,
)


def asked_have(last_utterance):
    if re.search(doyouhave_request, last_utterance["text"]) and about_virus(last_utterance):
        return True
    return False


def return_fact(facts, used_phrases, asked_about_age=False, met_last=False):
    for fact in facts:
        if all([fact not in j for j in used_phrases]):
            if fact != facts[-1] and not met_last:
                fact = improve_phrase(fact, asked_about_age, met_last)
            return fact
    return ""


def book_movie_music_confidence(confidence, last_utterance):
    threshold = 0.9
    if book_movie_music_found(last_utterance):
        logging.info("Found book/movie/music in user utterance - dropping confidence")
        confidence = min(confidence, threshold)
    return confidence


class CoronavirusSkillScenario:
    def __init__(self):
        try:
            num_cases, num_cv_deaths = get_cases_deaths()
            num_flu_deaths = 560000
            millionaire_number = 46800000
            self.phrases = make_phrases(num_cases, num_cv_deaths, num_flu_deaths, millionaire_number)
            self._updating_thread = threading.Thread(target=get_state_cases)
            self._updating_thread.start()
            logger.info("waiting for intital data 30s")
            time.sleep(30)
            logger.info("waiting for intital data 30s: DONE")
            # self.facts = [j.lower() for j in FACT_LIST]
            self.facts = [j for j in FACT_LIST]
            self.symptom_phrase = (
                "According to the CDC website, "
                "The main warning signs of coronavirus are: "
                "difficulty breathing or shortness of breath, "
                "persistent pain or pressure in the chest , "
                "new confusion or inability to arouse, "
                "bluish lips or face. If you develop any of these signs,"
                "get a medical attention. "
            )
            self.advice_phrase = (
                "Unfortunately, I am not allowed to give any recommendations "
                "about coronavirus. You can check the CDC website for more info"
            )
            self.advice_asthma_phrase = (
                "As you have asthma, I know that you should be especially cautious "
                "about coronavirus. " + self.advice_phrase
            )
        except Exception as e:
            logger.exception("Exception while retrieving new info about coronavirus")
            sentry_sdk.capture_exception(e)

    def __call__(self, dialogs):
        global STATE_DATA, COUNTY_DATA, NATION_DATA
        texts = []
        confidences = []
        human_attributes, bot_attributes, attributes = [], [], []

        for dialog in dialogs:
            reply, confidence, attr = "", 0, {}
            human_attr = dialog["human"]["attributes"]
            human_attr["coronavirus_skill"] = human_attr.get("coronavirus_skill", {})
            human_attr["coronavirus_skill"]["used_phrases"] = human_attr["coronavirus_skill"].get("used_phrases", [])
            bot_attr = {}
            human_attr["used_links"] = human_attr.get("used_links", defaultdict(list))
            try:
                confidence = 0
                if len(dialog["utterances"]) >= 2:
                    last_bot_phrase = dialog["utterances"][-2]["text"].lower()
                    stay_home_request = is_staying_home_requested(dialog["utterances"][-2], dialog["utterances"][-1])
                else:
                    last_bot_phrase = ""
                    stay_home_request = False

                prev_bot_uttr = dialog["bot_utterances"][-1] if len(dialog["bot_utterances"]) else {}
                last_utterance = dialog["utterances"][-1]
                last_utterance_text = last_utterance["text"].lower()
                last_utterances = []
                #  logging.info('*#*')
                #  logging.info([j['text'] for j in dialog['utterances']])
                min_back_len = len(dialog["utterances"])
                #  logging.info(min_back_len)
                for i in range(1, min_back_len, 2):
                    if len(dialog["utterances"]) >= i:
                        last_utterances.append(dialog["utterances"][-i]["text"].lower())
                last_bot_phrases = []
                for i in range(2, min_back_len, 2):
                    if len(dialog["utterances"]) >= i:
                        last_bot_phrases.append(dialog["utterances"][-i]["text"].lower())
                last_bot_phrase = ""
                if len(last_bot_phrases) > 0:
                    last_bot_phrase = last_bot_phrases[0]
                # this is questionable: it is wrong to lowercase responses, but needed to match data.
                met_last = any([self.facts[-1].lower() in j for j in human_attr["coronavirus_skill"]["used_phrases"]])
                logging.info(last_bot_phrases)
                logging.info(met_last)
                asked_about_age = any(
                    ["what is your age" in j for j in human_attr["coronavirus_skill"]["used_phrases"]]
                )
                #  logging.info(asked_about_age)
                if quarantine_end(last_utterance):
                    logging.info("Quarantine end detected")
                    reply, confidence = QUARANTINE_END_PHRASE, 0.95
                elif last_bot_phrase in [WORK_AND_STAY_HOME_PHRASE, CDC_STAY_HOME_RECOMMENDATION]:
                    if " why " in last_utterance_text or last_utterance_text[:3] == "why":
                        reply, confidence = EXPLAIN_PHRASE, 0.95
                elif dontlike(last_utterance):
                    reply, confidence = "", 0
                elif asked_have(last_utterance):
                    reply, confidence = BOT_CORONAVIRUS_PHRASE, 0.95
                    reply = improve_phrase(reply)
                elif vaccine_safety_request(last_utterance):
                    reply, confidence = VACCINE_SAFETY_PHRASE, 0.95
                elif emotion_detected(last_utterance, "fear") or emotion_detected(last_utterance, "anger"):
                    r = random()
                    if r < 0.5:
                        reply, confidence = FEAR_HATE_REPLY1, 0.95
                    else:
                        reply, confidence = FEAR_HATE_REPLY2, 0.95
                    reply = improve_phrase(reply)
                elif get_chance_request(last_utterance):
                    reply, confidence = (
                        "As I am not your family doctor, "
                        "my knowledge about your resilience to coronavirus is limited.",
                        0.95,
                    )
                    reply = f"{reply} Please, check the CDC website for more information."  # Daniil suggestion
                elif "to learn more" in last_bot_phrase:
                    fear_prob = get_emotions(dialog["utterances"][-1], probs=True).get("fear", 0)
                    logging.debug(f"Fear prob {fear_prob}")
                    if is_no(last_utterance):
                        logging.info("Another fact request detected, answer is NO")
                        reply = corona_switch_skill_reply()
                        confidence = 0.98
                        human_attr["coronavirus_skill"]["stop"] = True
                    elif fear_prob > 0.9:
                        logging.info("Corona fear detected")
                        reply = "Just stay home, wash your hands and you will be fine. We will get over it."
                        confidence = 0.95
                    elif is_yes(last_utterance):
                        logging.info("Returning a fact")
                        reply, confidence = (
                            return_fact(
                                self.facts, human_attr["coronavirus_skill"]["used_phrases"], asked_about_age, met_last
                            ),
                            1,
                        )
                    else:
                        reply, confidence = "", 0
                elif know_symptoms(last_utterance) and about_coronavirus(last_utterance):
                    logging.info("Symptom request detected")
                    reply, confidence = self.symptom_phrase, 1
                    reply = improve_phrase(reply, asked_about_age, met_last)
                elif asked_cure(last_utterance):
                    reply, confidence = CURE_REPLY, 0.9
                    reply = improve_phrase(reply, asked_about_age, met_last)
                elif "asthma" in last_utterance["text"]:
                    reply, utterance = self.advice_asthma_phrase, 1
                    reply = improve_phrase(reply, asked_about_age, met_last)
                elif wants_advice(last_utterance) and about_coronavirus(last_utterance):
                    logging.info("Advice request detected")
                    reply, confidence = self.advice_phrase, 1
                    reply = improve_phrase(reply, asked_about_age, met_last)
                elif any([j in last_bot_phrase for j in (["do you want to learn more"] + FACT_LIST)]):
                    logging.info("Bot offered another fact in previous utterance")
                    if is_yes(last_utterance):
                        logging.info("Answer is YES")
                        reply, confidence = (
                            return_fact(
                                self.facts, human_attr["coronavirus_skill"]["used_phrases"], asked_about_age, met_last
                            ),
                            1,
                        )
                        logging.info("No fact returned")
                        if not reply:
                            reply, confidence = "", 0
                    else:
                        logging.info("Answer is not YES")
                        reply, confidence = "", 0
                elif stay_home_request:
                    if is_yes(last_utterance):
                        reply, confidence = WORK_AND_STAY_HOME_PHRASE, 1.0
                    elif is_no(last_utterance):
                        reply, confidence = CDC_STAY_HOME_RECOMMENDATION, 1.0
                else:
                    detected_state = None
                    nation_names = list(NATION_DATA.keys())
                    state_names = list(STATES.keys())
                    county_names = [j[0].lower() for j in COUNTIES.keys()]
                    city_names = list(CITIES.keys())
                    total_names = nation_names + state_names + county_names + city_names
                    if "suppose you are asking about" in last_bot_phrase and is_yes(last_utterance):
                        logging.info("Detecting state by 1st&2nd utt")
                        tolook_utterances = last_utterances
                    else:  # Looking only on the first utterance
                        logging.info("Detecting state by 1st utt")
                        tolook_utterances = last_utterances[:1]
                    for utterance in tolook_utterances:
                        utt1 = utterance
                        for punct in punctuation:
                            utt1 = utt1.replace(punct, " ")
                            utt1 = " " + utt1 + " "
                        for state_name in total_names:
                            name1 = " " + state_name + " "
                            if name1 in utt1 and detected_state is None:
                                detected_state = state_name
                    logging.info("Detected state")
                    logging.info(detected_state)
                    logging.debug("Utterances")
                    logging.debug(tolook_utterances)
                    repeat_in_reply = False
                    if detected_state is None:  # No state dialog
                        if about_virus(last_utterance) and not about_coronavirus(last_utterance):
                            logging.info("About virus, not coronavirus")
                            reply, confidence = "I suppose you are asking about coronavirus. Is it right?", 1
                        else:
                            wants_cv = is_yes(last_utterance) and "you are asking about coronavirus" in last_bot_phrase
                            #  logging.info(last_bot_phrases)
                            not_seen_before = all(
                                ["confirmed cases of" not in j for j in human_attr["coronavirus_skill"]["used_phrases"]]
                            )
                            #  logging.info(not_seen_before)
                            was_firstphrase = is_yes(last_utterance) and "the number of millionaires" in last_bot_phrase
                            about_death = check_about_death(last_utterance)
                            is_age = False
                            if "is your age" in last_bot_phrase or "didn't get your age" in last_bot_phrase:
                                logging.info("I have just asked about age, returning age phrase")
                                reply, bot_attr, human_attr = get_age_answer(last_utterance, bot_attr, human_attr)
                                confidence = 1
                                if reply == "":
                                    logging.info("Could not detect age. Looking for something else")
                                    repeat_in_reply = True
                                else:
                                    is_age = True
                            if not is_age:
                                if was_firstphrase or about_death or repeat_in_reply:
                                    logging.info("I was asked about death or I offered second core fact")
                                    reply, confidence = self.phrases[1], 1.0
                                    reply = improve_phrase(reply, asked_about_age, met_last)

                                elif (wants_cv or about_coronavirus(last_utterance)) and not_seen_before:
                                    logging.info("Returning first phrase")
                                    reply, confidence = self.phrases[0], 1
                                    # DOESNT' NEED IMPROVEMENT
                                else:
                                    if is_yes(last_utterance):
                                        logging.info("YES received - returning fact")
                                        reply, confidence = (
                                            return_fact(
                                                self.facts,
                                                human_attr["coronavirus_skill"]["used_phrases"],
                                                asked_about_age,
                                                met_last,
                                            ),
                                            1,
                                        )
                                        if not reply:
                                            logging.debug("No reply received")
                                            reply, confidence = "", 0
                                    elif asked_origin(last_utterance) and about_coronavirus(last_utterance):
                                        logging.info("Origin phrase")
                                        reply, confidence = ORIGIN_PHRASE, 0.98
                                    elif asked_whatvirus(last_utterance):
                                        logging.info("What phrase")
                                        reply, confidence = WHAT_PHRASE, 0.98
                                        reply = improve_phrase(reply, asked_about_age, met_last)
                                    else:
                                        logging.info("Final point detected. Return smth")
                                        reply, confidence = (
                                            return_fact(
                                                self.facts,
                                                human_attr["coronavirus_skill"]["used_phrases"],
                                                asked_about_age,
                                                met_last,
                                            ),
                                            0.9,
                                        )
                    else:  # Detected some state
                        if about_virus(last_utterance) and not about_coronavirus(last_utterance):
                            logging.info("Detected some state, received question about virus")
                            reply = "I suppose you are asking about " "coronavirus in {0}. Is it right?".format(
                                detected_state
                            )
                            confidence = 0.99
                        else:
                            wants_cv = all(
                                [is_yes(last_utterance), "you are asking about coronavirus in" in last_bot_phrase]
                            )
                            wasnot_first = "of registered coronavirus" not in last_bot_phrase
                            if "is your age" in last_bot_phrase or "didn't get your age" in last_bot_phrase:
                                logging.info("After asking about age returning age phrase")
                                reply, bot_attr, human_attr = get_age_answer(last_utterance, bot_attr, human_attr)
                                confidence = 1
                            # Reply is empty if it wasnt about age.
                            if is_switch_topic(last_utterance) or is_no(last_utterance):
                                # We shut up under this condition, otherwise carry on
                                confidence = 0
                            elif (wants_cv or about_coronavirus(last_utterance)) and wasnot_first:
                                logging.info("Returning state phrase")
                                reply, confidence = (
                                    get_statephrase(detected_state, STATE_DATA, COUNTY_DATA, NATION_DATA),
                                    0.95,
                                )
                                reply = improve_phrase(reply, asked_about_age, met_last)
                            else:
                                if is_yes(last_utterance):
                                    logging.info("YES detected - returning fact")
                                    reply, confidence = (
                                        return_fact(
                                            self.facts,
                                            human_attr["coronavirus_skill"]["used_phrases"],
                                            asked_about_age,
                                            met_last,
                                        ),
                                        1,
                                    )
                                    if not reply:
                                        logging.info("NO detected - returning zero")
                                        reply, confidence = "", 0
                                else:
                                    logging.debug("Final point")
                                    reply, confidence = "", 0
                confidence = book_movie_music_confidence(confidence, last_utterance)
                if reply.lower() == last_utterance["text"].lower():
                    logging.info("Not to self repeat, drop confidence to 0")
                    confidence = 0
                elif reply == "":
                    logging.info("reply is empty, drop confidence to 0")
                    confidence = 0
                elif human_attr["coronavirus_skill"].get("stop", False) and CORONA_SWITCH_BEGIN not in reply:
                    logging.info("User not wants to talk about covid")
                    confidence = 0
                elif if_chat_about_particular_topic(last_utterance, prev_bot_uttr) and not about_virus(
                    last_utterance["text"]
                ):
                    logging.info("Topic chat request found, drop confidence to 0")
                    confidence = 0
                elif reply.lower() in last_utterances and confidence == 1:
                    logging.info("I have said that before, a bit less confident")
                    confidence = 0.5
                else:
                    logging.info("No special cases")

            except Exception as e:
                logger.exception("exception in coronavirus skill")
                sentry_sdk.capture_exception(e)
                reply = ""
                confidence = 0
            texts.append(reply)
            # add reply only once in the end to make code simpler
            human_attr["coronavirus_skill"]["used_phrases"].append(reply)
            confidences.append(confidence)
            human_attributes.append(human_attr)
            bot_attributes.append(bot_attr)
            attributes.append(attr)

        return texts, confidences, human_attributes, bot_attributes, attributes
