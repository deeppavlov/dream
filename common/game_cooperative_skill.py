import re

GAMES_COMPILED_PATTERN = re.compile(r"(\bgame\b|\bgames|videogame|\bgaming)", re.IGNORECASE)


def skill_trigger_phrases():
    return ["If you want to talk about games just say, \"let's talk about games\""]
