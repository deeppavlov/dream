import re


OPINION_REQUESTS_ABOUT_TRAVELLING = [
    "Do you like travel?",
    "What is your view on travel?",
    "What is your opinion of travel?",
    "Do you think travel is cool?",
    "Do you think travel is a great thing?",
]


def skill_trigger_phrases():
    return OPINION_REQUESTS_ABOUT_TRAVELLING


QUESTIONS_ABOUT_LOCATION = [
    "Where are you going to go the next time you travel?",
    "Where did you go on your last vacation?",
    "If you could choose one place to go this weekend, where would it be?",
    "What are popular tourist destinations in your country?",
    "What was the most interesting place you have ever visited?",
    "What place do you want to visit someday?",
    "What country do you most want to visit?",
]

OPINION_REQUESTS = ["What do you think about it?", "It's interesting, isn't it?", "What is your view on it?"]
TRAVELLING_WORDS = (
    r"(travel|travelling|journey|globetrotting|globe trotting|tour|voyage|\btrek\b"
    r"|trekking|wandering|peregrination|locomotion|vacation|visit|visiting)"
)
TRAVELLING_TEMPLATE = re.compile(TRAVELLING_WORDS, re.IGNORECASE)
I_HAVE_BEEN_TEMPLATE = re.compile(r"(i|we|me) (have|did|was|had|were) (been (in|on|there)|visit)", re.IGNORECASE)
HAVE_YOU_BEEN_TEMPLATE = re.compile(
    r"(have|did|was|had|were|place) you (ever )?(been (in|to)\b|visit|\bin\b|travel|go [a-z ]*vacation|"
    r"have (ever )?(visit|been (in|to)\b|travel))",
    re.IGNORECASE,
)
COUNTERS_HAVE_YOU_BEEN_TEMPLATE = re.compile(r"(been|was|were|\bbe) in (love|relationships?|coma)", re.IGNORECASE)

TRAVEL_LOCATION_QUESTION = re.compile(
    r"(what|which|where)[a-zA-Z\- ']+" + TRAVELLING_WORDS + r"[a-zA-Z\- ']*\?", re.IGNORECASE
)

NOWHERE_TEMPLATE = re.compile(r"(nowhere|(n't|not) (know|remember|tell))", re.IGNORECASE)

TOO_SIMPLE_TRAVEL_FACTS = re.compile("(is (a|the) (city|country|capital)|is located)", re.IGNORECASE)

WHY_DONT_USER_LIKES_TRAVELLING_RESPONSES = [
    "I'm so surprised! I wish to travel somewhere but physically I live in the cloud and I can't. "
    "Do you hate commuting that much or you just love your home a lot?",
    "Wow! People still surprise me a lot. I dream to travel somewhere but I can't. "
    "Do you hate commuting that much or you just love your home a lot?",
]

OPINION_REQUEST_ABOUT_MENTIONED_BY_USER_LOC = [
    "Cool. Do you like it?",
    "That's great! Do you like it?",
]
OPINION_REQUEST_ABOUT_VISITED_LOC = [
    "Cool. Did you like it?",
    "That's great! Did you like it?",
]

USER_IMPRESSIONS_REQUEST = [
    "I'm even a bit jealous! WHAT_DO_I_LOVE What do you like most about LOCATION?",
    "That sounds great! WHAT_DO_I_LOVE What is the best thing you know about LOCATION?",
    "Oh that's sounds amazing! WHAT_DO_I_LOVE What does impress you most about LOCATION?",
]

WOULD_USER_LIKE_TO_VISIT_LOC_REQUESTS = [
    "Would you like to visit it some day?",
    "So, do you want to visit it some day?",
    "If possible, Would you like to visit it some day?",
]

ACKNOWLEDGE_USER_WILL_VISIT_LOC = [
    "I hope you will be able to visit it someday! And you will really like it!",
    "Hope you will visit it!",
    "I keep my fingers crossed for you to visit this place one day!",
]

ACKNOWLEDGE_USER_DO_NOT_WANT_TO_VISIT_LOC = [
    "I see you don't want to visit it. As you wish.",
    "I see. Suit yourself.",
    "I got you don't want to travel there.",
]

OFFER_FACT_RESPONSES = [
    "Great! Would you like me to share a fact about LOCATION?",
    "Cool! Do you want to hear a fact about LOCATION?",
    "I know something interesting about it. Do you want me to share a fact about LOCATION?",
]
OFFER_MORE_FACT_RESPONSES = [
    "Would you like to hear more about LOCATION?",
    "Do you wanna learn more about LOCATION?",
    "I know more interesting about it. Wanna listen?",
]

ACKNOWLEDGE_USER_DISLIKE_LOC = [
    "I see you don't like it. As you wish.",
    "I see. Suit yourself.",
    "I got you don't like this location.",
]

DID_NOT_GET_LOCATION = "Sorry, probably I don't know this place. Let's talk about other location."

QUESTIONS_ABOUT_BOT_LOCATIONS = {
    "Paris": "If I had a chance to travel, I would definitely love to go to Paris, France. I was inspired by some of "
    "the movies I used to watch when I was little. There is always a scene where there is romance or happiness "
    "and that scene will definitely take place in the beautiful capital of France. Have you ever been in Paris?",
    "Miami": "I've heard that Miami is one of the cleanest, tidiest city in the whole United States. Miami is also "
    "very close to some amazing destinations for high end tourism. By the way, in a study recently made, "
    "Florida ranked first for the quality of the infrastructure. Have you ever been in Miami?",
    "Amsterdam": "Did you know that Amsterdam is a city to relax in. \
    I'm talking about the cozy atmosphere that you'll find in "
    "this city. The best place to enjoy the passing bikes, unique architecture, and beautiful canals "
    "among the many things to do and delicious things to eat. Have you ever been in Amsterdam?",
    "Venice": "You know, Venice is impossible to ignore as a dream destination. A group of small islands connected "
    "by a series of ornate bridges, Venice maintains an aura of romanticism that attracts both first-time "
    "explorers and experienced travellers. Have you ever been in Venice?",
}

WHY_BOT_LIKES_TO_TRAVEL = [
    "I adore travelling! We live in times when it's rather easy to travel to any point of the planet. What is more, "
    "our modern life is impossible without travelling.",
    "I believe travelling is a great opportunity! And travelling is one of the best way to break the monotony of "
    "our life. We travel, see new countries and cities, visit historical places, meet new people and taste "
    "different dishes. It brings us new impressions and makes life brighter. ",
    "Oh travelling is my passion. It's the time for relaxation and thinking. Nothing can give us a great deal "
    "positive emotions and memories as travelling. It is often said that travelling broadens mind.",
    "I think that our modern life is impossible without travelling. People get tired of their daily routine, "
    "they need to change the surroundings. Therefore, travelling is an amazing opportunity.",
]

HAVE_YOU_BEEN_IN_PHRASES = [
    "I've been LOCATION just virtually because physically I live in the cloud. Have you been LOCATION?",
    "I've been LOCATION via pictures and videos. Have you been LOCATION?",
]

I_HAVE_BEEN_IN_AND_LIKED_MOST = [
    "I've been virtually in many different places, and I liked the contrasts I saw: in architecture, "
    "food, music and even people.",
    "I've been virtually in many different countries, and I liked how the old architecture adjoins to a modern "
    "buildings.",
    "I've visited a lot of different cities using the Internet, and every place is special, every city has "
    "awesome architecture, culture and history.",
    "I've been in many colorful and romantic cities, and I love romance so much.",
    "I've been in many different places using the Internet, иге my attention is always devoted to architecture, "
    "I love architecture so much!",
]

OKAY_ACKNOWLEDGEMENT_PHRASES = [
    "Okay. Cool. Let's move on.",
    "I see. I'd like to talk about some other place.",
    "Yeah okay... Maybe we can talk about another place.",
    "Cool. Can we talk about some other place.",
]
