import re
import json

with open('common/presidents.json', 'r') as f:
    pres_dict = json.load(f)
    presidents = pres_dict['presidents']

swear_words = ['shit', 'son of a bitch', 'pussy', 'dickhead', 'dick', 'bastard', 'fuck', 'cunt', "stupid", "suck", 'idiot', 'moron']

PRESIDENT_OPINION_PATTERN = re.compile(r"\b(what do you think (about|of).*?|what.*?opinion.*?|do you like|i hate|fuck) (" + ("|".join(presidents) + ")"), re.IGNORECASE)

SWEAR_WORDS_PATTERN = re.compile(r"\b(you.*? (" + ("|".join(swear_words) + ")|fuck you)"), re.IGNORECASE)