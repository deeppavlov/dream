import re


OPINION_REQUESTS_ABOUT_TRAVELLING = ["Do you like travel?",
                                     "What is your view on travel?",
                                     "What is your opinion of travel?",
                                     "Do you think travel is cool?",
                                     "Many people say they adore travel. Do you agree?",
                                     "Do you think travel is a great thing?"
                                     ]

OFFER_TALK_ABOUT_TRAVELLING = ["Would you like to talk about travel?",
                               "Let's chat about travel adventures! Do you agree?",
                               "I'd like to talk about travel, would you?"
                               ]


def skill_trigger_phrases():
    return OPINION_REQUESTS_ABOUT_TRAVELLING + OFFER_TALK_ABOUT_TRAVELLING


QUESTIONS_ABOUT_LOCATION = ["What other places did you visit?",
                            "Where are you going to go the next time you travel?",
                            "Where did you go on your last vacation?",
                            "If you could choose one place to go this weekend, where would it be?",
                            "What are popular tourist destinations in your country?",
                            "What was the most interesting place you have ever visited?",
                            "What place do you want to visit someday?",
                            "What country do you most want to visit?"
                            ]

OPINION_REQUESTS = ["What do you think about it?",
                    "It's interesting, isn't it?",
                    "What is your view on it?"
                    ]

TRAVELLING_TEMPLATE = re.compile(r"(travel|travelling|journey|globetrotting|globe trotting|tour|voyage|\btrek\b"
                                 r"|trekking|wandering|peregrination|locomotion|vacation|visit|visiting)",
                                 re.IGNORECASE)
I_HAVE_BEEN_TEMPLATE = re.compile(r"(i|we|me) (have|did|was|had|were) (been (in|on|there)|visit)",
                                  re.IGNORECASE)
HAVE_YOU_BEEN_TEMPLATE = re.compile(r"(have|did|was|had|were) you (ever )?(been|visit|\bin\b|travel)",
                                    re.IGNORECASE)

WHY_DONT_USER_LIKES_TRAVELLING_RESPONSES = [
    "I'm so surprised! I wish to travel somewhere but physically I live in the cloud and I can't. "
    "Do you hate commuting that much or you just love your home a lot?",
    "Wow! People still surprise me a lot. I dream to travel somewhere but I can't. Why don't you like it?"
]

OPINION_REQUEST_ABOUT_MENTIONED_BY_USER_LOC = ["Cool. Do you like it?",
                                               "That's great! Do you like it?",
                                               "Wow! What is your view about it?",
                                               ]

USER_IMPRESSIONS_REQUEST = [
    "I'm even a bit jealous! What do you like most about this place?",
    "That's cool that you like it! What is the best thing you know about it?",
    "I'm glad you liked it! What does impress you most about this place?"
]

WOULD_USER_LIKE_TO_VISIT_LOC_REQUESTS = ["Would you like to visit it some day?",
                                         "So, do you want to visit it some day?",
                                         "If possible, Would you like to visit it some day?",
                                         ]

ACKNOWLEDGE_USER_WILL_VISIT_LOC = ["I hope you will be able to visit it someday! And you will really like it!",
                                   "Hope you will visit it!",
                                   "I keep my fingers crossed for you to visit this place one day!",
                                   ]

ACKNOWLEDGE_USER_DO_NOT_WANT_TO_VISIT_LOC = ["I see you don't want to visit it. As you wish.",
                                             "I see. Suit yourself.",
                                             "I got you don't want to travel there.",
                                             ]

OFFER_FACT_RESPONSES = ["Great! Would you like to me to share a fact about LOCATION?",
                        "Cool! Do you want to hear a fact about LOCATION?",
                        "I know something interesting about it. Do you want me to share a fact about LOCATION?",
                        ]

ACKNOWLEDGE_USER_DISLIKE_LOC = ["I see you don't like it. As you wish.",
                                "I see. Suit yourself.",
                                "I got you don't like this location.",
                                ]
