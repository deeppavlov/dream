import re

TOPIC_PATTERNS = {
    "animals": re.compile(r"(\banimals?|\bwilds?|leopards?|\blions?|beasts?)", re.IGNORECASE),
    "books": re.compile(r"(\bbooks?\b|\bread|literature|journal|magazine|novel)", re.IGNORECASE),
    "cars": re.compile(r"(\bcars?\b|automobile|driving|drive)", re.IGNORECASE),
    "depression": re.compile(r"(depress|stress|melanchol|doldrum|heaviness)", re.IGNORECASE),
    "family": re.compile(r"(\bhusband|\bwife|\bspouse|\bfamily|\bkids?\b|\bchild\b|\bchildren"
                         r"|\b(grand)?(ma|mom|mother|father|pa|dad|parent|daughters?|sons?|child)\b)", re.IGNORECASE),
    "food": re.compile(r"(\bfood|\beat(ing|s)?\b|\bcook(s|ed|ing)?\b)", re.IGNORECASE),
    "life": re.compile(r"(\blife|\blife style|\blifestyle)", re.IGNORECASE),
    "love": re.compile(r"(\blove|\bloving|\bbeloved|\bfriend|\brelationship|\brelation|\bwomen|\bmen\b"
                       r"|\bgirlfriend|\bboyfriend)", re.IGNORECASE),
    "me": re.compile(r"(\babout me\b|\bmyself)", re.IGNORECASE),
    "movies": re.compile(r"(\bmovie|\bcinema|\bcartoon|\bseries|\btv\b|\bcinematography|\byoutube|\banime"
                         r"|\bwatch)", re.IGNORECASE),
    "music": re.compile(r"(\bmusic|\bsongs?|\bsing(ing|er)?\b)", re.IGNORECASE),
    "news": re.compile(r"news", re.IGNORECASE),
    "pets": re.compile(r"(\bpets?\b|\bdogs?\b|\bcats?\b|\bpupp(y|ies)\b)", re.IGNORECASE),
    "politics": re.compile(r"(\bpolitic|\bpolicy)", re.IGNORECASE),
    "science": re.compile(r"(\bscience|\bresearch|\bsurvey|\btechnolog|\bdiscover|\bopening|\bbreakthrough"
                          r"|\bsci( |\-)?tech)", re.IGNORECASE),
    "school": re.compile(r"(\bschool|\bstudy|\beducation|\bexams?\b|\bexamination|\blearning|\bhomework)",
                         re.IGNORECASE),
    "sex": re.compile(r"(\bsex|\bporn\b|\bporno|\bdicks?\b|\bvagina|\bpuss(y|ies)\b|\bcocks?\b"
                      r"|\bmasturbat)", re.IGNORECASE),
    "sports": re.compile(r"(\bsport|\bfootball|\bbaseball|\bbasketball|\bhockey|\bsoccer)", re.IGNORECASE),
    "star wars": re.compile(r"(\bstar war\b|\bstar wars\b|\bsky walker|\bskywalker|\byoda)", re.IGNORECASE),
    "superheroes": re.compile(r"(\bsuperhero|\bsuper hero|\bhero(es|ism)?\b|\bmarvel|\bnemesis|\bvigilante|\bvillain"
                              r"|\bsidekick|\bcomics)", re.IGNORECASE),
    "travel": re.compile(r"(\btravel|\bjourney|\btour(ism|ists?|s)?\b|\btrips?\b|\bvoyage)", re.IGNORECASE),
    "donald trump": re.compile(r"(\btrump|\bdonald trump|\bamerican president|\bthe president)", re.IGNORECASE),
    "video games": re.compile(r"(\bvideo ?game|\bgam(e|es|ing)\b|\bplay ?station|\bminecraft|\bgta\b)", re.IGNORECASE),
    "weather": re.compile(r"(\bweather|\bforecast)", re.IGNORECASE),
    "work": re.compile(r"(\bwork(ed|ing|s)?|\bjob\b|\boccupation|\bprofession)", re.IGNORECASE),
    "you": re.compile(r"(\babout you\b|\byourself|\bsocialbot|\babout alexa\b|\byou alexa\b"
                      r"|\b(this|that|amazon|current|alexa) (competition|challenge))", re.IGNORECASE),
}
