import json
import logging
import re

from common.utils import get_named_locations
from tools.city_slot import OWMCitySlot
from tools.weather_service import weather_forecast_now

from scenario.constants import BLACKLISTED_LOCATIONS

logger = logging.getLogger(__name__)

with open("data/weather_questions.json", "r", encoding="utf-8") as f:
    WEATHER_DICT = json.load(f)

CITY_SLOT = OWMCitySlot()


def retrieve_location_entity_from_utterance(human_utter: dict) -> str:
    """Gets the first extracted entity from an utterance dict

    :param human_utter: a human utterance
    :type human_utter: dict
    :return: a string with city name or an empty string if the extraction failed
    :rtype: str
    """

    location_name = ""
    if "text" in human_utter:
        location_name = CITY_SLOT(human_utter["text"])
    if not location_name and "annotations" in human_utter:
        locations = get_named_locations(human_utter)
        if locations:
            location_name = locations[-1]
    if location_name.lower().strip() in BLACKLISTED_LOCATIONS:
        location_name = ""
    return location_name


def request_weather_service(location_name, timeperiod=None) -> None:
    """Bridge func that calls the weather service to get a forecast

    :param location_name:
    :param timeperiod:
    """
    logger.info("requesting weather for %s at %s" % (location_name, timeperiod))
    return weather_forecast_now(location_name)


def get_preferred_weather(request: str, weather_dict: dict) -> str:
    """Extracts a weather type from user's request

    :param request: a human utterance
    :type request: str
    :param weather_dict: a dictionary containing aliases for weather types
    :type: dict
    :return: a weather type or an empty string if the extraction failed
    :rtype: str
    """

    detected_weather = ""
    for weather in weather_dict.keys():
        re_weather = r".*" + r"|".join(["(" + s + ")" for s in weather_dict[weather]["synonyms"]]) + r"( |,|\.|$)"
        if re.match(re_weather, request.lower()):
            detected_weather = weather
    return detected_weather
