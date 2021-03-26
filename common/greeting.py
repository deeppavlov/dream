import re

HI_THIS_IS_ALEXA = "Hi, this is an Alexa Prize Socialbot!"

HOW_ARE_YOU_RESPONSES = [
    "How are you?",
    "How are things?",
    "How are you doing today?",
    "How is the day going so far for you?",
]

WHAT_IS_YOUR_NAME_RESPONSES = [
    "I think we have not met yet. What name would you like me to call you?",
    "I do not think we have met before. What name would you like me to call you?",
    "I'd love to get to know you a bit better before we chat! What is your name?",
]

TOPIC_OFFERING_TEMPLATES = ["TOPIC1 and TOPIC2 are my favorite topics.",
                            "Maybe, TOPIC1 or TOPIC2?",
                            "Say, TOPIC1 or TOPIC2?",
                            "How about TOPIC1 or TOPIC2?"
                            ]

GREETING_QUESTIONS = {
    "what_to_talk_about": ["What do you want to talk about?",
                           "What would you want to talk about?",
                           "What would you like to chat about?",
                           "What do you wanna talk about?",
                           "What are we gonna talk about?",
                           "What's on your mind?"
                           ],
    "what_are_your_interests": ["What are your interests?",
                                "What do you like?",
                                "What things excite you?",
                                # "What's cool?"
                                ],
    "what_are_your_hobbies": ["What are your hobbies?",
                              "What do you like to do in your free time?",
                              "Which things capture your imagination?",
                              "What are the things you love to spend your spare time with?",
                              "How do you like to spend your spare time?"
                              ],
    "recent_personal_events": ["What happened in your life recently?",
                               "What's happening?",
                               "What's going on?",
                               "What's up?"
                               ]
}

dont_tell_you_templates = re.compile(
    r"(\bno\b|\bnot\b|\bnone\b|nothing|anything|something|"
    r"(n't|not) (know|remember|tell|share|give|talk|want|wanna)|"
    r"(\bi|\bi'm) ?(do|did|will|am|can)?(n't| not))", re.IGNORECASE)


def dont_tell_you_answer(annotated_phrase):
    if re.search(dont_tell_you_templates, annotated_phrase["text"]):
        return True
    return False


HOW_BOT_IS_DOING_RESPONSES = [
    "I can't complain! It's against the Company Policy."
    "I am as happy as a clam in butter sauce.",
    "I am fine thanks!",
    "I'm so happy I have to sit on my hands to keep from clapping.",
    "Blessed!",
    "I'm rocking pretty hard. I'd give myself about a seven and a half. Maybe an eight.",
    "Fantastic!",
    "Outstanding!",
    "I'm better than I was, but not nearly as good as I'm going to be.",
    "Spectacular, by all reports!",
    "I'm living the dream.",
    "I'm so happy I can hardly stand myself.",
    "Amazing.... and I've got written testimonials.",
    "Just another day in Paradise. Thanks for asking.",
    "Not too bad for an AI living inside your Echo!",
    "Very well, thank you.",
    "I am functioning within acceptable parameters.",
    "About as good as can be expected.",
    "Reasonably well, thank you."
]

LIST_ACTIVITIES_OFFER = "Do you want to know what I can do?"

GOOD_MOOD_REACTIONS = [
    "Cool!",
    "I am happy for you!",
    "I am glad for you!",
    "Sounds like a good mood!"
]

BAD_MOOD_REACTIONS = [
    "I am sorry to hear that.",
    "I see.",
    "Sounds like a bad mood.",
    "Sounds like a bad mood."
]

GIVE_ME_CHANCE_TO_CHEER_UP = [
    "Let me try to entertain you.",
    "Let me try to cheer you up.",
    "Give me a chance to cheer you up."
]

LIST_ACTIVITIES_RESPONSE = "I'm a socialbot running inside Alexa, and I'm all about chatting with people like you. " \
                           "I can answer questions, share fun facts, discuss movies, books and news."
