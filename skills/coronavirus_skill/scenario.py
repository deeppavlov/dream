import logging
from os import getenv
import sentry_sdk
import requests

sentry_sdk.init(getenv('SENTRY_DSN'))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
CORONAVIRUS_URL = 'https://www.worldometers.info/coronavirus/coronavirus-cases/'


def is_yes(annotated_phrase):
    return annotated_phrase['annotations']['intent_catcher'].get('yes', {}).get('detected') == 1


def about_coronavirus(annotated_phrase):
    contain_words = all([j in annotated_phrase['text'] for j in ['corona', 'virus']])
    contain_related = any([j in annotated_phrase['text'] for j in ['virus', 'outbreak', 'pandemy', 'epidemy',
                                                                   'pandemi', 'epidemi']])
    return contain_words or contain_related


def get_cases_deaths(coronavirus_url):
    data = requests.get(coronavirus_url)
    num_cases = data.text.split('<strong><a href="/coronavirus/">')[1].split(' ')[0].replace(',', '')
    num_deaths = data.text.split('coronavirus/coronavirus-death-toll/"><strong>')[1].split(' ')[0].replace(',', '')
    return int(num_cases), int(num_deaths)


def make_phrases(n_cases, n_deaths, num_flu_deaths, millionair_number):
    n_times1 = millionair_number // n_cases
    n_times2 = num_flu_deaths // n_deaths
    nums1 = [n_cases, n_times1]
    nums2 = [n_deaths, n_times2]
    phrase1 = 'According to the most recent data, {0} people have ever contacted coronavirus. ' \
              'This is about {1} times less than the number of millionaires, ' \
              'so you are not likely to contact it any time soon. ' \
              'Do you want to know another fact about it?'.format(*nums1)
    phrase2 = 'According to the most recent data, {0} people have ever died from coronavirus. ' \
              'This is  about {1} times less than the number of Americans ' \
              'died from flu last winter, so you are not likely to die from it any time soon. \
           After all, you have lived through the last winter somehow!'.format(*nums2)
    return [phrase1, phrase2]


class CoronavirusSkillScenario:

    def __init__(self):
        try:
            num_cases, num_cv_deaths = get_cases_deaths(CORONAVIRUS_URL)
            num_flu_deaths = 80000
            millionaire_number = 46800000
            self.phrases = make_phrases(num_cases, num_cv_deaths, num_flu_deaths, millionaire_number)
        except Exception as e:
            logger.exception('Exception while retrieving new info about coronavirus')
            sentry_sdk.capture_exception(e)

    def __call__(self, dialogs):
        texts = []
        confidences = []
        for dialog in dialogs:
            try:
                if len(dialog['utterances']) >= 2:
                    last_bot_phrase = dialog['utterances'][-2]['text']
                else:
                    last_bot_phrase = ''
                last_utterance = dialog['utterances'][-1]
                if about_coronavirus(last_utterance):
                    reply, confidence = self.phrases[0], 0.95
                elif is_yes(last_utterance) and 'you are not likely to contact it any time soon' in last_bot_phrase:
                    reply, confidence = self.phrases[1], 1.0
                else:
                    reply, confidence = '', 0

            except Exception as e:
                logger.exception("exception in coronavirus skill")
                sentry_sdk.capture_exception(e)
                reply = ""
                confidence = 0
            texts.append(reply)
            confidences.append(confidence)

        return texts, confidences  # , human_attributes, bot_attributes, attributes
