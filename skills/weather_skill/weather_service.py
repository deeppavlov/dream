import logging
import sentry_sdk
from os import getenv
import requests
import random

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
# Temperature coneversion constants
KELVIN_OFFSET = 273.15
FAHRENHEIT_OFFSET = 32.0
FAHRENHEIT_DEGREE_SCALE = 1.8


def random_crazy_forecast(city_str):
    """
    This function produces joke-like response with funny weather forecast.

    May be launched in case of problems with Basic service or in case of bad LOCation recognition
    :param city_str:
    :return: weather forecast as string for Human
    """

    # just a list of crazy forecasts:
    crazy_description = random.choice(["Fish rain may occur.",
                                       "Skittles chewies falling is possible.",
                                       "Toy Godzilla may come to the city.",
                                       "Potato storm may wonder you.",
                                       "Pancake tornado may be seen in the sky",
                                       "magic powder from the sky",
                                       "rainbow leaks may occur",
                                       "Teletubbies invasion is still probable",
                                       "Chuk Norris' thunderstorm may be unexpected occasion",
                                       "Hyperbolic UFOs may be flying over the sky tonight",
                                       "Santa Claus dance may cause tickling feeling under the nose",
                                       "Drunk deer may knock the roof"
                                       ])

    temperature_prediction = random.randrange(0, 100)

    template = "Currently I have problems with getting weather in %s. But I would guess... %s . " \
               "And the temperature may be around %d fahrenheit. Would you enjoy it?" % (
                   city_str, crazy_description, temperature_prediction)
    return template


def kelvin_to_fahrenheit(kelvintemp):
    """
    # taken from
    # https://github.com/csparpa/pyowm/blob/9ee1f88818d6be154865cc7447f2f6708a37227b/pyowm/utils/temputils.py

    Converts a numeric temperature from Kelvin degrees to Fahrenheit degrees
    :param kelvintemp: the Kelvin temperature
    :type kelvintemp: int/long/float
    :returns: the float Fahrenheit temperature
    :raises: *TypeError* when bad argument types are provided
    """
    if kelvintemp < 0:
        raise ValueError(__name__ + ": negative temperature values not allowed")
    fahrenheittemp = (kelvintemp - KELVIN_OFFSET) * FAHRENHEIT_DEGREE_SCALE + FAHRENHEIT_OFFSET
    return float("{0:.2f}".format(fahrenheittemp))


def owm_requests_weather_forecast_now(city_str):
    """Simple service for openweathermap.org

    :param city_str: string with city name
    :return: response for user as string

    Result Example:
        {
            "coord":
                {"lon":-0.13,"lat":51.51},
            "weather": [
                {
                    "id":300,
                    "main":"Drizzle",
                    "description":"light intensity drizzle",
                    "icon":"09d"}
                ],
            "base":"stations",
            "main":
                {
                "temp":280.32,
                "pressure":1012,
                "humidity":81,
                "temp_min":279.15,
                "temp_max":281.15},
            "visibility":10000,
            "wind":
                {
                "speed":4.1,
                "deg":80},
            "clouds":{
                "all":90},
            "dt":1485789600,
            "sys":{
                "type":1,"id":5091,"message":0.0103,
                "country":"GB",
                "sunrise":1485762037,
                "sunset":1485794875},
            "id":2643743,
            "name":"London",
            "cod":200
        }
    """
    api_key = "644515bef5492fff0a5913f73ac212ae"
    url = "http://api.openweathermap.org/data/2.5/weather?q=%s&appid=%s" % (city_str, api_key)
    try:
        resp = requests.get(url=url, timeout=2)
        json_data = resp.json()
        try:
            description = json_data['weather'][0]['description']

            temperature = kelvin_to_fahrenheit(json_data['main']['temp'])
            # min_temperature = kelvin_to_fahrenheit(json_data['main']['temp_min'])
            # max_temperature = kelvin_to_fahrenheit(json_data['main']['temp_max'])

            city_name = json_data['name']

            # meter/sec
            wind_speed = json_data['wind']['speed']

            # hPa
            # pressure = json_data['main']['pressure']
            # humidity = json_data['main']['humidity']

            response_template = "It is %s, temperature is around %0.1f in %s. " \
                                "Wind speed is about %f meters per second" % (
                                    description, temperature, city_name, wind_speed)
        except Exception as e:
            # we have problems with weather service:
            # soltions:
            # 1. say sorry and recomend to try later
            # 2. use another weather provider?
            logger.exception("WeatherService Problems")
            sentry_sdk.capture_exception(e)
            response_template = random_crazy_forecast(city_str)
            # response_template = SORRY_TEMPLATE

    except (requests.ConnectTimeout, requests.ReadTimeout) as e:
        sentry_sdk.capture_exception(e)
        logger.exception("WeatherService Timeout")
        response_template = SORRY_TEMPLATE
    # print(response_template)
    return response_template
