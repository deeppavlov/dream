import re
import json

with open('common/presidents.json', 'r') as f:
    pres_dict = json.load(f)
    presidents = pres_dict['presidents']

swear_words = ['shit', 'son of a bitch', 'pussy', 'dickhead', 'dick', 'bastard', 'fuck', 'cunt']

PRESIDENT_OPINION_PATTERN = re.compile(r"\b(what do you think about|what.*? opinion.*?|do you like ) (" + ("|".join(presidents) + ")"), re.IGNORECASE)

SWEAR_WORDS_PATTERN = re.compile(r"\b(you.*? (" + ("|".join(swear_words) + ")|fuck you)"), re.IGNORECASE)