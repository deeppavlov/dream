from common.utils import is_yes


ASK_WEATHER_SKILL_FOR_HOMELAND_PHRASE = "Would you like to know the weather there?"
ASK_WEATHER_SKILL_PHRASE = "Would you like to know the weather?"


def skill_trigger_phrases():
    return [ASK_WEATHER_SKILL_PHRASE]


def is_weather_for_homeland_requested(prev_bot_utt, user_utt):
    if ASK_WEATHER_SKILL_FOR_HOMELAND_PHRASE.lower() in prev_bot_utt.get('text', '').lower():
        if is_yes(user_utt):
            return True
    return False


def is_weather_without_city_requested(prev_bot_utt, user_utt):
    if ASK_WEATHER_SKILL_PHRASE.lower() in prev_bot_utt.get('text', '').lower():
        if is_yes(user_utt):
            return True
    return False


def is_weather_requested(prev_bot_utt, user_utt):
    w1 = is_weather_for_homeland_requested(prev_bot_utt, user_utt)
    w2 = is_weather_without_city_requested(prev_bot_utt, user_utt)
    return w1 or w2
