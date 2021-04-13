import re

GAMES_COMPILED_PATTERN = re.compile(r"(\bgame\b|\bgames|videogame|\bgaming)", re.IGNORECASE)
TRIGGER_PHRASES = ["do you love video games?"]


def skill_trigger_phrases():
    return TRIGGER_PHRASES


def game_skill_was_proposed(prev_bot_utt):
    return any([phrase.lower() in prev_bot_utt.get("text", "").lower() for phrase in TRIGGER_PHRASES])
