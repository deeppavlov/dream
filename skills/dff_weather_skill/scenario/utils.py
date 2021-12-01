import json
import re

from common.utils import get_named_locations
from scenario.constants import BADLISTED_LOCATIONS
from tools.city_slot import OWMCitySlot
from tools.weather_service import weather_forecast_now

with open("data/weather_questions.json", "r", encoding="utf-8") as f:
    WEATHER_DICT = json.load(f)

CITY_SLOT = OWMCitySlot()


def retrieve_location_entity_from_utterance(human_utter: dict) -> str:
    """Get the first extracted entity from an utterance dict.

    :param human_utter: a human utterance
    :type human_utter: dict
    :return: a string with city name or an empty string if an extraction failed
    :rtype: str
    """
    location_name = ""
    if "text" in human_utter:
        location_name = CITY_SLOT(human_utter["text"])
    if not location_name and "annotations" in human_utter:
        locations = get_named_locations(human_utter)
        if locations:
            location_name = locations[-1]
    if location_name.lower().strip() in BADLISTED_LOCATIONS:
        location_name = ""
    return location_name


def request_weather_service(location_name: str) -> str:
    """Call the weather service to get a forecast.

    :param location_name: string with a location name
    :type location_name: str
    :return: a forecast for a given location
    :rtype: str
    """
    return weather_forecast_now(location_name)


def get_preferred_weather(request: str, weather_dict: dict) -> str:
    """Extract a weather type from user's request.

    :param request: a human utterance
    :type request: str
    :param weather_dict: a dictionary containing aliases for weather types
    :type weather_dict: dict
    :return: a weather type or an empty string if the extraction failed
    :rtype: str
    """
    preferred_weather = ""
    for weather in weather_dict.keys():
        synonyms = "|".join([f"({s})" for s in weather_dict[weather]["synonyms"]])
        re_weather = rf".*({synonyms})([\s,\.]+|$)"
        if re.match(re_weather, request.lower()):
            preferred_weather = weather
    return preferred_weather
