import logging
import sentry_sdk
from os import getenv
import requests

sentry_sdk.init(getenv('SENTRY_DSN'))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


def weather_forecast_now(city_str):
    """
    Interface method encapsulating implementation of weather service
    Return a weather forecast in some city"""
    # to use CoBotQA as weather provider:
    # return cobotqa_weather_forecast_now(city_str)
    # to use openweathermap.org as weather provider:
    # return openweathermap_pure_url_weather_forecast_now(city_str)
    return owm_requests_weather_forecast_now(city_str)


def dummy_weather_forecast_now(city_str):
    """Return a weather forecast in some city"""
    return "Weather in %s is good. 5 above zero" % city_str


def cobotqa_weather_forecast_now(city_str, timeperiod=None):
    """Warpper that requests cobotQA for weather
    But cobot is often fails...
    """
    # TODO add support of tomorrow requests
    question_string = "what is the weather in %s" % city_str

    ##########################################################################################
    # setup CoBotQA envs and import it
    import sys
    import os
    # os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ruler_bot.settings")
    SELF_DIR = os.path.dirname(os.path.abspath(__file__))
    SKILLS_DIR = os.path.dirname(SELF_DIR)
    COBOTQA_DIR = SKILLS_DIR + "/CoBotQA"
    sys.path.append(COBOTQA_DIR)

    os.environ.setdefault("COBOT_API_KEY", "MYF6T5vloa7UIfT1LwftY3I33JmzlTaA86lwlVGm")
    os.environ.setdefault("COBOT_QA_SERVICE_URL",
                          "https://06421kpunk.execute-api.us-east-1.amazonaws.com/prod/qa/v1/answer")
    ##########################################################################################

    from cobotqa_service import send_cobotqa
    print("requesting cobot for: %s" % question_string)
    response = send_cobotqa(question_string)
    print("cobot response: %s" % response)
    return response


SORRY_TEMPLATE = "Sorry, we have a problem with the weather service. Try again a little bit later."


def owm_requests_weather_forecast_now(city_str):
    """Simple service for openweathermap.org

    :param city_str: string with city name
    :return: response for user as string
    """
    api_key = "644515bef5492fff0a5913f73ac212ae"
    url = "http://api.openweathermap.org/data/2.5/weather?q=%s&appid=%s" % (city_str, api_key)
    try:
        resp = requests.get(url=url, timeout=3)
        json_data = resp.json()
        try:
            description = json_data['weather'][0]['description']
            temperature = json_data['main']['temp']
            city_name = json_data['name']
            response_template = "It is %s, temperature: %0.1f in %s" % (
                description, temperature, city_name)
        except Exception as e:
            # we have problems with weather service:
            # soltions:
            # 1. say sorry and recomend to try later
            # 2. use another weather provider?
            logger.exception("WeatherService Problems")
            sentry_sdk.capture_exception(e)
            response_template = SORRY_TEMPLATE

    except (requests.ConnectTimeout, requests.ReadTimeout) as e:
        sentry_sdk.capture_exception(e)
        logger.exception("WeatherService Timeout")
        response_template = SORRY_TEMPLATE
    # print(response_template)
    return response_template
