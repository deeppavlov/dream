import logging
import random
from os import getenv

import requests


WEATHER_SERVICE_TIMEOUT = 2
OPENWEATHERMAP_API_KEY = getenv("OPENWEATHERMAP_API_KEY")
if OPENWEATHERMAP_API_KEY is None:
    raise RuntimeError("OPENWEATHERMAP_API_KEY environment variable is not set")
OPENWEATHERMAP_URL = "http://api.openweathermap.org/data/2.5/weather?q=%s&appid=%s"
SORRY_TEMPLATE = "Sorry, we have a problem with the weather service. Try again a little bit later."
# Temperature conversion constants
KELVIN_OFFSET = 273.15
FAHRENHEIT_OFFSET = 32.0
FAHRENHEIT_DEGREE_SCALE = 1.8

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def weather_forecast_now(city_str: str) -> str:
    """Call the weather service to provide a weather forecast.

    :param city_str: a city name
    :type city_str: str
    :return: a weather forecast
    :rtype: str
    """
    return owm_requests_weather_forecast_now(city_str)


def dummy_weather_forecast_now(city_str: str) -> str:
    """Provide a dummy weather forecast in a given city.

    :param: a city name
    :type: str
    :return: a dummy forecast
    :rtype: str
    """
    return "Weather in %s is good. 5 above zero" % city_str


def random_crazy_forecast(city_str: str) -> str:
    """Provide a joke-like response with a funny weather forecast in case of problems with the service.

    :param city_str: a city name
    :type city_str: str
    :return: weather forecast as string for Human
    :rtype: str
    """
    crazy_description = random.choice(
        [
            "Fish rain may occur.",
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
            "Drunk deer may knock the roof",
        ]
    )
    temperature_prediction = random.randrange(2, 100)
    template = (
        "Currently I have problems with getting weather in %s. But I would guess... %s . "
        "And the temperature may be around %d degrees Fahrenheit. Would you enjoy it?"
        % (city_str, crazy_description, temperature_prediction)
    )
    return template


def kelvin_to_fahrenheit(kelvin_temp: float) -> float:
    """Convert temperature in Kelvin to Fahrenheit.

    This code taken from:
    https://github.com/csparpa/pyowm/blob/9ee1f88818d6be154865cc7447f2f6708a37227b/pyowm/utils/temputils.py

    :param kelvin_temp: a temperature in Kelvin
    :type kelvin_temp: float
    :returns: a temperature in Fahrenheit
    :rtype: float
    :raises ValueError: if a negative number is given
    """
    if kelvin_temp < 0:
        raise ValueError(__name__ + ": negative temperature values not allowed")
    fahrenheit_temp = (kelvin_temp - KELVIN_OFFSET) * FAHRENHEIT_DEGREE_SCALE + FAHRENHEIT_OFFSET
    return float("{0:.2f}".format(fahrenheit_temp))


def owm_requests_weather_forecast_now(city_str: str) -> str:
    """Access openweathermap.org to provide a forecast.

    Response example from openweathermap.org:
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

    :param city_str: a city name
    :type city_str: str
    :return: a forecast or the sorry template in case of problems with the service
    :rtype: str
    """
    url = OPENWEATHERMAP_URL % (city_str, OPENWEATHERMAP_API_KEY)
    try:
        resp = requests.get(url=url, timeout=WEATHER_SERVICE_TIMEOUT)
        json_data = resp.json()
        try:
            if "weather" in json_data:
                description = json_data["weather"][0]["description"]
                temperature = kelvin_to_fahrenheit(json_data["main"]["temp"])
                city_name = json_data["name"]
                wind_speed = json_data["wind"]["speed"]
                if abs(temperature) == 1.0:
                    degree_str = "degree"
                else:
                    degree_str = "degrees"
                response_template = (
                    "It is %s, temperature is around %0.1f %s Fahrenheit in %s. "
                    "Wind speed is about %0.1f meters per second"
                    % (description, temperature, degree_str, city_name, wind_speed)
                )
            else:
                response_template = random_crazy_forecast(city_str)
        except ValueError:
            response_template = random_crazy_forecast(city_str)
            logger.exception("Negative temperature given.")
        except LookupError:
            response_template = random_crazy_forecast(city_str)
            logger.exception("Error occurred while parsing weather service response.")
    except requests.exceptions.RequestException as e:
        logger.exception(e)
        response_template = SORRY_TEMPLATE
    return response_template
