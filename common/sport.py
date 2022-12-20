import re
from common.utils import get_topics, TOPIC_GROUPS


##################################################################################################################
# LINK
##################################################################################################################


BINARY_QUESTION_ABOUT_SPORT = ["Do you like sports?", "Do you like fitness?", "Would you like to chat about sport?"]
BINARY_QUESTION_ABOUT_ATHLETE = ["Would you like to talk about your favorite athletes? ", "Do you have a sports idol?"]

BINARY_QUESTION_ABOUT_COMP = ["Well, Do you want to talk about sports competitions?"]


def skill_trigger_phrases():
    return BINARY_QUESTION_ABOUT_SPORT + BINARY_QUESTION_ABOUT_ATHLETE + BINARY_QUESTION_ABOUT_COMP


##################################################################################################################
# TEMPLATE
##################################################################################################################


SUPER_CONFIDENCE = 1.0
HIGH_CONFIDENCE = 0.99
DEFAULT_CONFIDENCE = 0.9
LOW_CONFIDENCE = 0.75
ZERO_CONFIDENCE = 0.0

NUMBER_PROBABILITY = 0


SPORTS_NO_ING = (
    r"\b(aerobics|archery|badminton|baseball|basketball|beach volleyball|biathlon"
    r"|billiards|canoe|car race|chess|climb|coach|cricket"
    r"|curling|cycle|darts|dive|draughts"
    r"|fence|figure skate|football|golf|gymnastics|handball|hang glide"
    r"|high jump|hockey|hurdle race|ice rink|in-line skate|jog|judo|karate"
    r"|long jump|martial arts|motorbike sports|mountaineer|orienteer"
    r"|parachute|pole-vault|polo|ride|rowing|rugby|ski|snooker"
    r"|track-and-field|triathlon|tug of war|volleyball|water polo|waterski"
    r"|weight lift|work out|wrestle|run|swim|tennis|fitness|lacrosse|ballet|soccer)\b"
)
# curling in SPORTS_NO_ING is not a mistake - there is not word to curl
ING_FORMS = {
    "run": "running",
    "swim": "swimming",
    "ski": "skiing",
    "dive": "diving",
    "box": "boxing",
    "canoe": "canoeing",
    "climb": "climbing",
    "cycle": "cycling",
    "fence": "fencing",
    "figure skate": "figure skating",
    "in-line skate": "figure skating",
    "hang glide": "hand gliding",
    "high jump": "high jumping",
    "jog": "jogging",
    "ride": "riding",
    "row": "rowing",
    "weight lift": "weight lifing",
    "wrestle": "wrestling",
    "work out": "working out",
    "mountaineer": "mountaineering",
    "dance": "dancing",
    "orienteer": "orienteering",
    "parachute": "parachuting",
    "pole-vault": "pole-vaulting",
    "car race": "car racing",
    "wakeboard": "wakeboarding",
    "long jump": "long jumping",
}
REVERSE_ING_FORMS = {ING_FORMS[key]: key for key in ING_FORMS}
regexp_ing_forms = r"|".join([rf"\b{k}" for k in ING_FORMS.values()])
SPORTS = rf"({regexp_ing_forms}|{SPORTS_NO_ING})"
KIND_OF_SPORTS_TEMPLATE = re.compile(
    SPORTS,
    re.IGNORECASE,
)
PASSIVE_SPORT = ["chess", "checkers"]

OPINION_ABOUT_PASSIVE_SPORT = [
    "KIND_OF_SPORT is cool. But since I live in the cloud, I can only play PASSIVE_SPORT!",
    "I would like to play KIND_OF_SPORT. " "But I have no physical incarnation, so I can only play PASSIVE_SPORT!",
]

KIND_OF_COMPETITION_TEMPLATE = re.compile(
    r"(FIFA World Cup|Olympic Games|Super Bowl|Grand National"
    r"|Masters Tournament|Wimbledon|Kentucky Derby|NBA"
    r"|Cricket World Cup|World Series|Tour De France|March Madness"
    r"|UEFA|Ryder Cup|Daytona 500|Rugby World Cup"
    r"|Boston Marathon|Open Championship|Indianapolis 500|Stanley Cup"
    r"|Monaco Grand Prix|Rose Bowl|UFC|NFL)",
    re.IGNORECASE,
)

ATHLETE_TEMPLETE = re.compile(
    r"(athlete|sportsperson|games player|muscle person|player" r"|footballer|aquanaut|diver|jock|lifter)", re.IGNORECASE
)
SPORT_TEMPLATE = re.compile(r"(sport|active)", re.IGNORECASE)
SUPPORT_TEMPLATE = re.compile(r"(support|a fan of)", re.IGNORECASE)

QUESTION_TEMPLATE = re.compile(r"(what|did|do|which|who) (team )?(you )?(do|is|are|kind of|know|like)", re.IGNORECASE)

LIKE_TEMPLATE = re.compile(r"(like|love|support|a fan of|favorite|enjoy|want to talk)?", re.IGNORECASE)

HATE_TEMPLATE = re.compile(r"(hate)", re.IGNORECASE)

COMPETITION_TEMPLATE = re.compile(r"(tournament|tourney|competition|championship|derby)", re.IGNORECASE)

OFFER_FACT_COMPETITION = [
    "I recently wandered on the Internet and found an interesting fact about COMPETITION." "Do you want to hear?",
    "Cool! Do you want to hear a fact about COMPETITION?",
    "I know something interesting about it. Do you want me to share a fact about COMPETITION?",
]
OPINION_REQUESTS = ["What do you think about it?", "It's interesting, isn't it?", "What is your view on it?"]

ASK_ABOUT_ATH_IN_KIND_OF_SPORT = [
    "Yep, that's cool. I'm really wondering who is your idol in KIND_OF_SPORT?",
    "Wow, that's cool. Who is your favorite athlete in KIND_OF_SPORT?",
]

OPINION_ABOUT_ATHLETE_WITH_TEAM_AND_POS = [
    "Oh, I know this POSITION from TEAM. He does his job well.",
    "Oh, I kind of know him. He is a POSITION and plays in TEAM.",
]

OPINION_ABOUT_ATHLETE_WITH_TEAM = [
    "Oh yes, he's cool. I've seen him perform miracles in TEAM.",
    "Oh, he's just a wizard. He does his job well in TEAM.",
]

OPINION_ABOUT_ATHLETE_WITHOUT_TEAM = ["I know NAME. He's kind of from COUNTRY. Have you ever been in COUNTRY?"]

OPINION_ABOUT_TEAM = ["By the way, I support the TEAM. I remember how they won in COMPETITION. It was cool."]

LAST_CHANCE_TEMPLATE = [
    "I'm still too young and I don't know much, but something tells me that It's very interesting. "
    "Tell me more about that",
    "Oh, this is the first time I hear about this. " "Tell me more about that",
    "This is probably very interesting. Tell me more about that.",
]


def about_sport(annotated_utterance):
    found_topics = get_topics(annotated_utterance, probs=False, which="all")
    if any([topic in found_topics for topic in TOPIC_GROUPS["sport"]]):
        return True
    elif re.findall(KIND_OF_SPORTS_TEMPLATE, annotated_utterance["text"]):
        return True
    elif re.findall(KIND_OF_COMPETITION_TEMPLATE, annotated_utterance["text"]):
        return True
    else:
        return False
