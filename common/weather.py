import re
from common.utils import is_yes, get_intents


ASK_WEATHER_SKILL_FOR_HOMELAND_PHRASE = "Would you like to know the weather there?"
ASK_WEATHER_SKILL_PHRASE = "Would you like to know the weather?"

WEATHER_COMPILED_PATTERN = re.compile(r"(weather|forecast)", re.IGNORECASE)
WEATHER_REQUEST_COMPILED_PATTERN = re.compile(
    r"((tell me|what is|what's|what about|to know|you know) (the )?weather)", re.IGNORECASE
)


def skill_trigger_phrases():
    return [ASK_WEATHER_SKILL_PHRASE]


def skill_all_trigger_phrases():
    # these phrases include linkto from skill_trigger_phrases, and some SPECIFIC linking phrases
    return skill_trigger_phrases() + [ASK_WEATHER_SKILL_FOR_HOMELAND_PHRASE, ASK_WEATHER_SKILL_PHRASE]


def is_weather_for_homeland_requested(prev_bot_utt, user_utt):
    if ASK_WEATHER_SKILL_FOR_HOMELAND_PHRASE.lower() in prev_bot_utt.get("text", "").lower():
        if is_yes(user_utt):
            return True
    return False


def is_weather_without_city_requested(prev_bot_utt, user_utt):
    if ASK_WEATHER_SKILL_PHRASE.lower() in prev_bot_utt.get("text", "").lower():
        if is_yes(user_utt):
            return True
    return False


def if_special_weather_turn_on(user_utt, prev_bot_utt):
    if (
        "weather_forecast_intent" in get_intents(user_utt, probs=False, which="all")
        or is_weather_for_homeland_requested(prev_bot_utt, user_utt)
        or is_weather_without_city_requested(prev_bot_utt, user_utt)
    ):
        return True
    return False
