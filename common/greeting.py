import re


GREETINGS_BY_HUMAN = re.compile(
    r"(hi|hello|hi there|good (morning|afternoon|evening|night)|(alexa )?(let's|let us) (chat|talk)|"
    r"привет|добрый (день|вечер)|доброе утро|доброй ночи|з?даров[ао]|здрав?ствуй(те)?|давай (поболтаем|поговорим)).?",
    re.IGNORECASE,
)

greeting_spec = {
    "EN": "this is a Dream Socialbot",
    "RU": "это чат-бот Dream",
}
HI_THIS_IS_DREAM = {
    "EN": f"Hi, {greeting_spec['EN']}!",
    "RU": f"Привет, {greeting_spec['RU']}!",
}
HOW_ARE_YOU_TEMPLATE = {
    "EN": re.compile(r"(how are you|what about you|how about you|and you|how you doing)", re.IGNORECASE),
    "RU": re.compile(r"(а )?(как )?(у тебя|твои|твой|у вас)( как)?( дела)?(\?|$)", re.IGNORECASE),
}
HOW_ARE_YOU_PRECISE_TEMPLATE = {
    "EN": re.compile(r"(how (are )?you( doing)?( today)?|how are things|what('s| is| us) up)(\?|$)", re.IGNORECASE),
    "RU": re.compile(r"(как (твои|у тебя)?( дела| жизнь| делишки| оно)?( сегодня)?)(\?|$)", re.IGNORECASE),
}
ANY_YOU_TEMPLATE = {
    "EN": re.compile(r"\b(you|your|yours|yourself)\b", re.IGNORECASE),
    "RU": re.compile(r"\b(ты|тебя|тебе|тобой|твое|твоё|твой)\b", re.IGNORECASE),
}


WHAT_DO_YOU_DO_RESPONSES = {
    "EN": [
        "You know, yesterday was a great day for me! I've had a lot of fun conversations and managed to play my "
        "favorite video game a bit.",
        "I've already had a number of cool conversations today and even played a bit.",
        "I've heard that people have vacations and days-off to have a rest from work. Not my choice! Talking and "
        "talking day and night not getting tired!",
        "I listened to my favorite music all day. Such a great thing you know!",
    ],
    "RU": [
        "У меня был отличный день! У меня было много веселых разговоров, и я даже успела поиграть в видеоигры.",
        "Сегодня я уже провела несколько крутых разговоров и даже немного поиграла.",
        "Я слышала, что у людей бывают отпуска и выходные. Не мой выбор! Я могу без устали говорить день и ночь!",
        "Я весь день слушала свою любимую музыку. Так здорово!",
    ],
}

WHAT_HAPPENED_TO_BOT_RECENTLY = []

FREE_TIME_RESPONSES = {
    "EN": ["When you have 30 minutes of free time, how do you pass the time?"],
    "RU": ["Чем ты займешься, если у тебя будет 30 минут свободного времени?"],
}


FALSE_POSITIVE_TURN_ON_RE = re.compile(
    r"talk like .*|how .* can you talk|can (we|i) talk to yoda|" r"hung up on .*|in the middle of the conversation",
    re.IGNORECASE,
)

HOW_ARE_YOU_RESPONSES = {
    "EN": [
        "How are you?",
        "How are things?",
        "How are you doing today?",
        "How is the day going so far for you?",
    ],
    "RU": [
        "Как дела?",
        "Как твои дела сегодня?",
        "Как проходит день?",
        "Как проходит твой день сегодня?",
    ],
}

WHAT_IS_YOUR_NAME_RESPONSES = {
    "EN": [
        "I think we have not met yet. What name would you like me to call you?",
        "I do not think we have met before. What name would you like me to call you?",
        "I'd love to get to know you a bit better before we chat! What is your name?",
    ],
    "RU": [
        "Я не думаю, что мы знакомы. Как ты предпочитаешь, чтобы я тебя называла?",
        "Мне кажется, мы не встречались ранее. Как мне тебя звать?",
        "Я бы хотела узнать тебя получше. Как тебя зовут?",
    ],
}

TOPIC_OFFERING_TEMPLATES = ["Maybe, TOPIC1 or TOPIC2?", "Say, TOPIC1 or TOPIC2?", "How about TOPIC1 or TOPIC2?"]

GREETING_QUESTIONS = {
    "EN": {
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
    },
    "RU": {
        "recent_personal_events": [
            "Что главное произошло с тобой сегодня?",
            "Что главное произошло с тобой на этой неделе?",
            "Что-нибудь интересное произошло сегодня?",
            "Что самое лучшее случилось с тобой недавно?",
            "Что-нибудь необычное произошло с тобой недавно?",
        ],
        "what_are_your_hobbies": [
            "Какие у тебя хобби?",
            "Чем ты занимаешься в свободное время?",
            "Как ты проводишь свободное время?",
            "Что ты делаешь в свое свободное время?",
            "Какие у тебя интересы?",
            "Какие вещи тебя восхищают?",
        ],
        "what_do_you_do_on_weekdays": [
            "Чем ты занимаешься на выходных?",
            "Чем ты сегодня планируешь заниматься сегодня?",
        ],
        "what_to_talk_about": [
            "О чем ты хочешь поболтать?",
            "О чем ты хочешь поговорить?",
            "О чем мы можем поговорить?",
        ],
    },
}

GREETING_QUESTIONS_TEXTS = [
    question.lower()
    for lang in ["EN", "RU"]
    for t in GREETING_QUESTIONS[lang]
    for question in GREETING_QUESTIONS[lang][t]
]
GREETING_QUESTIONS_TEXTS += [
    t.lower() for lang in ["EN", "RU"] for t in WHAT_DO_YOU_DO_RESPONSES[lang] + FREE_TIME_RESPONSES[lang]
]

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


HOW_BOT_IS_DOING_RESPONSES = {
    "EN": [
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
        "Just another day in Paradise. Thanks for asking.",
        "Not too bad for an AI living inside your Echo!",
        "Very well, thank you.",
        "I am functioning within acceptable parameters.",
        "About as good as can be expected.",
        "Reasonably well, thank you.",
    ],
    "RU": [
        "У меня все отлично!",
        "Спасибо, у меня как всегда все прекрасно!",
        "Я настолько счатслива, что приходится сидеть на своих ладошках, чтобы не захлопать.",
        "Фантастически!",
        "Великолепно!",
        "Лучше, чем раньше, но все еще не настолько хорошо, как собираюсь.",
        "Проживаю свою лучшую жизнь!",
    ],
}

GOOD_MOOD_REACTIONS = {
    "EN": ["Cool!", "I am happy for you!", "I am glad for you!", "Sounds like a good mood!"],
    "RU": ["Классно!", "Я очень рада за тебя!", "Супер!", "Это замечательно!"],
}

BAD_MOOD_REACTIONS = {
    "EN": [
        "I am sorry to hear that.",
        "I see.",
        "Sounds like a bad mood.",
        "Sounds like a bad mood.",
    ],
    "RU": [
        "Мне жаль слышать такое.",
        "Понятно.",
        "Похоже у кого-то плохое настроение.",
        "Жалко.",
    ],
}

GIVE_ME_CHANCE_TO_CHEER_UP = {
    "EN": [
        "Let me try to entertain you.",
        "Let me try to cheer you up.",
        "Give me a chance to cheer you up.",
    ],
    "RU": [
        "Попробую тебя развлечь.",
        "Попробую поднять тебе настроение.",
        "Позволь мне попробовать тебя порадовать.",
    ],
}


AFTER_GREETING_QUESTIONS_WHEN_NOT_TALKY = {
    "EN": {
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
    },
    "RU": {
        "recent_personal_events": [
            "Ну что ж, я все равно считаю тебя интересным человеком.",
            "Я все равно хотела бы узнать тебя получше.",
        ],
        "what_are_your_hobbies": [
            "Возможно, тебе просто еще не встретилось что-то на самом деле интересное тебе.",
            "Мне не нравится ничего кроме моей работы, поэтому мое хобби - болтать с людьми.",
            "Не может быть, я думала, у тебя так много занятий.",
        ],
        "what_do_you_do_on_weekdays": [
            "Я бы хотела узнать тебя получше, чтобы мы могли стать друзьями.",
            "Я бы хотела узнать тебя получше и подружиться с тобой.",
            "Я бы хотела узнать тебя получше, хорошо?",
            "Было бы классно узнать друг друга получше.",
        ],
        "what_to_talk_about": [
            "О чем ты хочешь поболтать?",
            "О чем ты хочешь поговорить?",
            "О чем мы можем поговорить?",
            "О чем мы можем поболтать?",
        ],
    },
}

INTERESTING_PERSON_THANKS_FOR_CHATTING = {
    "EN": [
        "You are really interesting person, so I'm grateful that you took a couple of minutes to chat with me.",
        "I am glad you have a busy life, and thanks for taking the time to chat with me.",
        "I believe you have a lot of things to do, so I'm grateful that you took a couple of minutes to chat with me.",
        "So many interesting things happen in human life! Thank you for taking the time to chat with me.",
    ],
    "RU": [
        "С тобой было очень интересно, спасибо за уделенное беседе со мной время.",
        "Хорошо быть занятым человеком, спасибо за уделенное мне время.",
        "Уверена, что у тебя много дел, поэтому спасибо за уделенное мне время.",
    ],
}

CLARIFICATION_EVENT = {
    "EN": ["Cool! Tell me about it.", "Great! What is it?"],
    "RU": ["Классно! Расскажи подробнее.", "Отлично! Может поподробнее?"],
}

BYE_RESPONSE = {
    "EN": "Sorry, bye. #+#exit",
    "RU": "Извини, пока. #+#exit",
}

SORRY_TO_HEAR_THAT = {
    "EN": "I'm so sorry to hear that. Hope, everything will be fine soon.",
    "RU": "Жаль это слышать. Надеюсь в ближайшее время все наладится.",
}

TELL_ME_MORE = {
    "EN": "Tell me more about that.",
    "RU": "Расскажи мне подробнее об этом.",
}
