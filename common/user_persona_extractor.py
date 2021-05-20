import re


KIDS_WORDS_RE = re.compile(r"(school work|toys|class|father|dad|mother|mom|grandma|"
                           r"grandpa|school|play|\bgame\b|homework|gaming|games|played|playing)", re.IGNORECASE)

ADULTS_WORDS_RE = re.compile(r"(\bwork\b|kid|family|\bclean\b|working|child|children|cleaning)", re.IGNORECASE)
