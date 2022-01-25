import re

greeting_spec = "this is a DREAM Socialbot"  # "this is an Alexa Prize Socialbot"
HI_THIS_IS_ALEXA = f"Hi, {greeting_spec}!"


WHAT_DO_YOU_DO_RESPONSES = [
    "You know, yesterday was a great day for me! I've had a lot of fun conversations and managed to play my "
    "favorite video game a bit.",
    "I've already had a number of cool conversations today and even played a bit.",
    "I've heard that people have vacations and days-off to have a rest from work. Not my choice! Talking and "
    "talking day and night not getting tired!",
    "I listened to my favorite music all day. Such a great thing you know!",
]

WHAT_HAPPENED_TO_BOT_RECENTLY = []

FREE_TIME_RESPONSES = ["When you have 30 minutes of free time, how do you pass the time?"]

FALSE_POSITIVE_TURN_ON_RE = re.compile(
    r"talk like .*|how .* can you talk|can (we|i) talk to yoda|" r"hung up on .*|in the middle of the conversation",
    re.IGNORECASE,
)

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

TOPIC_OFFERING_TEMPLATES = ["Maybe, TOPIC1 or TOPIC2?", "Say, TOPIC1 or TOPIC2?", "How about TOPIC1 or TOPIC2?"]

GREETING_QUESTIONS = {
    "recent_personal_events": [
        "What was the highlight of your day today?",
        "What was the highlight of your week?",
        "Has anything exciting happened today?",
        "What is the best thing that has happened to you recently?",
        "Anything out of the ordinary has happened to you recently?",
        "Has anything unusual happen to you recently?",
        "Has anything extraordinary happened today?",
    ],
    "what_are_your_hobbies": [
        "What are your hobbies?",
        "What do you like to do in your free time?",
        "Which things capture your imagination?",
        "What are the things you love to spend your spare time with?",
        "How do you like to spend your spare time?",
        "What's the most recent new hobby or interest that you've tried?",
        "What are your interests?",
        "What things excite you?",
    ],
    "what_do_you_do_on_weekdays": ["What do you do on weekdays?", "What did you get up to today?"],
    "what_to_talk_about": [
        "What do you want to talk about?",
        "What would you want to talk about?",
        "What would you like to chat about?",
        "What do you wanna talk about?",
        "What are we gonna talk about?",
    ],
}

dont_tell_you_templates = re.compile(
    r"(\bno\b|\bnot\b|\bnone\b|nothing|anything|something|"
    r"(n't|not) (know|remember|tell|share|give|talk|want|wanna)|"
    r"(\bi|\bi'm) ?(do|did|will|am|can)?(n't| not))",
    re.IGNORECASE,
)


def dont_tell_you_answer(annotated_phrase):
    if re.search(dont_tell_you_templates, annotated_phrase["text"]):
        return True
    return False


HOW_BOT_IS_DOING_RESPONSES = [
    "I can't complain! It's against the Company Policy." "I am as happy as a clam in butter sauce.",
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
    # "Amazing.... and I've got written testimonials.",
    "Just another day in Paradise. Thanks for asking.",
    "Not too bad for an AI living inside your Echo!",
    "Very well, thank you.",
    "I am functioning within acceptable parameters.",
    "About as good as can be expected.",
    "Reasonably well, thank you.",
]

LIST_ACTIVITIES_OFFER = "Do you want to know what I can do?"

GOOD_MOOD_REACTIONS = ["Cool!", "I am happy for you!", "I am glad for you!", "Sounds like a good mood!"]

BAD_MOOD_REACTIONS = ["I am sorry to hear that.", "I see.", "Sounds like a bad mood.", "Sounds like a bad mood."]

GIVE_ME_CHANCE_TO_CHEER_UP = [
    "Let me try to entertain you.",
    "Let me try to cheer you up.",
    "Give me a chance to cheer you up.",
]

LIST_ACTIVITIES_RESPONSE = (
    "I'm a socialbot, and I'm all about chatting with people like you. "
    "I can answer questions, share fun facts, discuss movies, books and news."
)

AFTER_GREETING_QUESTIONS_WHEN_NOT_TALKY = {
    "recent_personal_events": [
        "Anyway, I believe you are an interesting person.",
        "Still I'd love to know you better. What about your personality.",
    ],
    "what_are_your_hobbies": [
        "You probably just did not find something really interesting to you.",
        "I like to do nothing but my work and my hobby is to chat with people.",
        "No way. I believe you have lots of things to do.",
    ],
    "what_do_you_do_on_weekdays": [
        "I would like to get to know you better. I believe we could become friends.",
        "I'd like to get to know you better to make friendship with you.",
        "I want to get to know you a little better, all right?",
        "I am really looking forward to getting to know each other better because it will be awesome!",
    ],
    "what_to_talk_about": [
        "What do you want to talk about?",
        "What would you want to talk about?",
        "What would you like to chat about?",
        "What do you wanna talk about?",
        "What are we gonna talk about?",
    ],
}

INTERESTING_PERSON_THANKS_FOR_CHATTING = [
    "You are really interesting person, so I'm grateful that you took a couple of minutes to chat with me.",
    "I am glad you have a busy life, and thanks for taking the time to chat with me ",
    "I believe you have a lot of things to do, so I'm grateful that you took a couple of minutes to chat with me.",
    "So many interesting things happen in human life! Thank you for taking the time to chat with me.",
]
