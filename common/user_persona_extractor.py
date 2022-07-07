import re


# Any moment of conversation
KIDS_WORDS_RE = re.compile(
    r"(school work|\btoys|\bclass|father|\bdad\b|\bdaddy\b|mother|\bmom\b|\bmommy\b|"
    r"grandma|grandmother|grandfather|grandpa|"
    r"school|homework)",
    re.IGNORECASE,
)
# only after what do you do
KIDS_ACTIVITIES_RE = re.compile(r"(\bplay|\bgame\b|gaming|games|played|playing)", re.IGNORECASE)

# Any moment of conversation
ADULTS_WORDS_RE = re.compile(
    r"(\bwork\b|\bworking\b|\bgym\b|smoking|drunk|"
    r"husband|wife|\bmy child\b|my children\b|\bdaughters?\b|\bsons?\b)",
    re.IGNORECASE,
)
# only after what do you do
ADULTS_ACTIVITIES_RE = re.compile(
    r"(\bwork\b|kid|family|\bclean\b|working|child|children|cleaning|girlfriend|"
    r"boyfriend|husband|wife|house ?work|\bdaughters?\b|\bsons?\b)",
    re.IGNORECASE,
)
