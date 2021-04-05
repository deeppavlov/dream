import re

##################################################################################################################
# LINK
##################################################################################################################


BINARY_QUESTION_ABOUT_SPORT = ["Do you like sports?",
                               # "Do you think active lifestyle is cool?",
                               "Do you like fitness?",
                               "Would you like to chat about sport?"
                               ]
BINARY_QUESTION_ABOUT_ATHLETE = ["Would you like to talk about your favorite athletes?",
                                 "Do you have a sports idol?"
                                 ]

BINARY_QUESTION_ABOUT_COMP = ["Well, Do you want to talk about sports competitions?"]


def skill_trigger_phrases():
    return BINARY_QUESTION_ABOUT_SPORT + BINARY_QUESTION_ABOUT_ATHLETE + BINARY_QUESTION_ABOUT_COMP


##################################################################################################################
# TEMPLATE
##################################################################################################################


SUPER_CONFIDENCE = 1.0
HIGH_CONFIDENCE = 0.99
DEFAULT_CONFIDENCE = 0.9
ZERO_CONFIDENCE = 0.0

KIND_OF_SPORTS_TEMPLATE = re.compile(
    r"(aerobics|archery|badminton|baseball|basketball|beach volleyball|biathlon"
    r"|billiards|boxing|canoeing|car racing|chess|climbing|coach|cricket"
    r"|cross-country skiing|curling|cycling|darts|diving skiing|draughts"
    r"|fencing|figure skating|football|golf|gymnastics|handball|hang gliding"
    r"|high jump|hockey|hurdle race|ice rink|in-line skating|jogging|judo|karate"
    r"|long jump|martial arts|motorbike sports|mountaineering|orienteering"
    r"|parachuting|pole-vaulting|polo|riding|rowing|rugby|sailing|skis|snooker"
    r"|track-and-field|triathlon|tug of war|volleyball|water polo|waterski"
    r"|weight lifting|working out|wrestling|run|swim|fitness|lacrosse|riding horses|ballet|marching|soccer)",
    re.IGNORECASE,
)

KIND_OF_COMPETITION_TEMPLATE = re.compile(
    r"(FIFA World Cup|Olympic Games|Super Bowl|Grand National"
    r"|Masters Tournament|Wimbledon|Kentucky Derby|NBA"
    r"|Cricket World Cup|World Series|Tour De France|March Madness"
    r"|UEFA Champions League|Ryder Cup|Daytona 500|Rugby World Cup"
    r"|Boston Marathon|Open Championship|Indianapolis 500|Stanley Cup"
    r"|Monaco Grand Prix|Rose Bowl|MMA|UFC)",
    re.IGNORECASE,
)

ATHLETE_TEMPLETE = re.compile(
    r"(athlete|sportsperson|games player|muscle person|player"
    r"|footballer|aquanaut|diver|jock|lifter)", re.IGNORECASE
)
SPORT_TEMPLATE = re.compile(r"(sport|active)", re.IGNORECASE)
SUPPORT_TEMPLATE = re.compile(r"(support|a fan of)", re.IGNORECASE)

QUESTION_TEMPLATE = re.compile(r"(what|did|do|which|who) (team )?(you )?(do|is|are|kind of|know|like)", re.IGNORECASE)

LIKE_TEMPLATE = re.compile(r"(like|love|support|a fan of|favorite|enjoy|want to talk)?", re.IGNORECASE)

COMPETITION_TEMPLATE = re.compile(r"(tournament|tourney|competition)", re.IGNORECASE)
