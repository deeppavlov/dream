import re

from common.weather import ASK_WEATHER_SKILL_FOR_HOMELAND_PHRASE


def skill_trigger_phrases():
    return ["What is your name?", "Where are you from?", "Как тебя зовут?", "Откуда ты родом?"]


what_is_your_name_pattern = re.compile(
    r"((what is|what's|whats|tell me|may i know|ask you for) your? name|what name would you like|"
    r"как( я могу| могу)? (тебя|вас) (зовут|звать|называть)|какое (у тебя|твое|твоё) (имя|прозвище|название)|"
    r"как к тебе обращаться)",
    re.IGNORECASE,
)
my_name_is_pattern = re.compile(
    r"my (name is|name's)|call me|"
    r"мо[её] (имя [а-яА-ЯЙйЁё]+|прозвище|название)|меня зовут|(зови|называй) меня|обращайся ко мне",
    re.IGNORECASE,
)
_is_not_re = r"(is not|isn't|was not|wasn't|have (not|never) been|haven't been|had (not|never) been|hadn't been)"
my_name_is_not_pattern = re.compile(
    rf"(my (name {_is_not_re}|name's not)|(don't|not) call me|why do you call me|(that|this|it) {_is_not_re} my name|"
    rf"меня зовут (не\b|не так|по-другому|иначе)|меня (не так|по-другому|иначе) зовут|не (зови|называй) меня|"
    rf"мое имя не\b)",
    re.IGNORECASE,
)
where_are_you_from_pattern = re.compile(
    r"(where are you from|where you (were|was) born|"
    r"(what is|what's|whats|tell me) your (home\s?land|mother\s?land|native\s?land|birth\s?place)|"
    r"откуда ты( родом)?[.\?]?$|где ты (родился|вырос)[.\?]?$)",
    re.IGNORECASE,
)
my_origin_is_pattern = re.compile(
    r"(my ((home\s?land|mother\s?land|native\s?land|birth\s?place) is|"
    r"(home\s?land|mother\s?land|native\s?land|birth\s?place)'s)|(i was|i were) born in|i am from|i'm from|"
    r"я родом из|я вырос(ла)? в\b|я родил(ась|ся) в\b)",
    re.IGNORECASE,
)
what_is_your_location_pattern = re.compile(
    r"((what is|what's|whats|tell me) your? location|where do you live|where are you( now)?|is that where you live now|"
    r"где ты (сейчас )?(жив[её]шь|проживаешь|находишься|[.\?]?$))",
    re.IGNORECASE,
)
my_location_is_pattern = re.compile(
    r"(my (location is|location's)|(i am|i'm|i)( live| living)? in([a-zA-z ]+)?(now)|"
    r"я (живу|проживаю|нахожусь) в\b)",
    re.IGNORECASE,
)

_name_re = r"((first |last |middle |second )?name)"
_tell_re = r"(told|said|gave|tells|says|gives)|((have|had) (told|said|given))"
_you_know_question_re = r"(do|did|can|could) you (know|find out|learn)|(have|had) you (known|found out|learned|learnt)"
_how_re = r"(how|where|when|from whom)"
_i_live_re = r"(i lived?|my (house|home) (is|was|have been)|my family live[sd]?)"
_how_do_you_know = (
    rf"({_how_re} {_you_know_question_re}|who {_tell_re} you|" rf"кто (сказал|рассказал)|откуда (ты )?знаешь)"
)

how_do_you_know_my_info_patterns = {
    "name": re.compile(
        rf"{_how_do_you_know} (my {_name_re}|what is my {_name_re}|what my {_name_re} is|мо[её] имя|как меня зовут)",
        re.IGNORECASE,
    ),
    "location": re.compile(
        rf"{_how_do_you_know} (where {_i_live_re}|где я (живу|проживаю|нахожусь|сейчас))", re.IGNORECASE
    ),
    "homeland": re.compile(rf"{_how_do_you_know} (where i am from|откуда я (родом)?|где я вырос(ла)?)", re.IGNORECASE),
}

_common_secret_re = r"(((it|this|that) is (a )?|^)(secret|private|confidential)|(это |^)секрет|не скажу)"
is_secret_patterns = {
    "name": re.compile(rf"{_common_secret_re}|\b(sur)?name is (a )?(secret|private|confidential)", re.IGNORECASE),
    "location": re.compile(rf"{_common_secret_re}|location is (a )?(secret|private|confidential)", re.IGNORECASE),
    "homeland": re.compile(rf"{_common_secret_re}", re.IGNORECASE),
}

BOT_DOESNT_KNOW_INFO_KEY = "bot_doesnt_know_info"
BOT_KNOWS_INFO_KEY = "bot_knows_info"
how_do_you_know_my_info_responses = {
    "name": {
        BOT_DOESNT_KNOW_INFO_KEY: {
            "EN": "Sorry, but I really do not know your name. Would you be so kind to tell me you name?",
            "RU": "Извини, кажется, я еще не знаю, как тебя зовут. Если ты не против, скажи мне, как тебя зовут?",
        },
        BOT_KNOWS_INFO_KEY: {
            "EN": "Ah, you have probably forgotten that you told me your name before. "
            "Maybe you told me your name the last time we talked.",
            "RU": "Кажется, я уже знаю твое имя из прошлых бесед.",
        },
    },
    "location": {
        BOT_DOESNT_KNOW_INFO_KEY: {
            "EN": "Sorry, but I really do not know where you live. Would tell me?",
            "RU": "Извини, кажется я еще этого не знаю. Расскажешь мне, где ты живешь?",
        },
        BOT_KNOWS_INFO_KEY: {
            "EN": "Ah, you have probably forgotten that you told me where you live before. "
            "Maybe you told me this the last time we talked.",
            "RU": "Кажется, я уже знаю, где ты живешь из прошлых бесед.",
        },
    },
    "homeland": {
        BOT_DOESNT_KNOW_INFO_KEY: {
            "EN": "Sorry, but I really do not know where you are from. So, where are you from? "
            "I hope i am not tactless.",
            "RU": "Извини, но я еще не знаю, откуда ты. Расскажи мне, откуда ты родом?",
        },
        BOT_KNOWS_INFO_KEY: {
            "EN": "Ah, you have probably forgotten that you told me where you are from before. "
            "Maybe you told me this the last time we talked",
            "RU": "Кажется, я уже знаю, откуда ты, из прошлых бесед.",
        },
    },
}
MAX_READABLE_NAME_WORD_LEN = 20
NON_GEOGRAPHICAL_LOCATIONS_COMPILED_PATTERN = re.compile(
    r"\b(hospital|school|work|home|car|train|train station|outdoors|bed|kitchen|bedroom|bathroom|"
    r"basement|jail|prison|bath|больнице|школе|работе|дома|машине|поезде|станции|улице|кровати|"
    r"кухне|спальне|ванной|ванне|гостиной|тюрьме)\b",
    re.IGNORECASE,
)
ASK_GEOGRAPHICAL_LOCATION_BECAUSE_USER_MISUNDERSTOOD_BOT = {
    "homeland": {
        "EN": "Sorry, but I probably misheard you. "
        "I am just curious to know the region or the city in which you were born.",
        "RU": "Извини, кажется, я неверно поняла тебя. Мне просто было любопытно узнать, страну или город, откуда ты.",
    },
    "location": {
        "EN": "Sorry, but I probably misheard you. Could you please tell me in which city or region you are now?",
        "RU": "Извини, кажется, я неверно поняла тебя. Я просто хотела спросить, в какой стране или городе ты живешь?",
    },
}

RESPONSE_PHRASES = {
    "EN": {
        "name": ["Nice to meet you, "],
        "location": [ASK_WEATHER_SKILL_FOR_HOMELAND_PHRASE, "Cool!"],
        "homeland": ["Is that where you live now?", "Cool!"],
    },
    "RU": {
        "name": ["Приятно познакомиться, "],
        "location": ["Мне всегда нравилось узнавать новое о человеке!", "Классно!"],
        "homeland": ["А сейчас ты живешь в этом же месте?", "Круто!"],
    },
}

REPEAT_INFO_PHRASES = {
    "name": {
        "EN": "I didn't get your name. Could you, please, repeat it.",
        "RU": "Ой, я не смогла распознать имя. Можешь, пожалуйста, повторить.",
    },
    "location": {
        "EN": "I didn't get your location. Could you, please, repeat it.",
        "RU": "Ой, я не смогла распознать город или страну. Можешь, пожалуйста, повторить.",
    },
    "homeland": {
        "EN": "I didn't get where you have been born. Could you please repeat it?",
        "RU": "Ой, я не смогла распознать город или страну. Можешь, пожалуйста, повторить.",
    },
}

TELL_MY_COMPILED_PATTERNS = {
    "name": re.compile(
        r"(what is|what's|whats|tell me|you know|you remember|memorize|say) my name|how( [a-zA-Z ]+)?call me|"
        r"my name is what|you( can| could| shall| will)? tell my name|"
        r"как меня зовут|как мо[её] имя|как ты меня назвал|ты знаешь мо[её] имя",
        re.IGNORECASE,
    ),
    "location": re.compile(
        r"((what is|what's|whats|tell me|you know|you remember|memorize|say) my (location|country|city|town)|"
        r"where (am i|i am)(\snow)?|where( do)?i live|where( am)?i( am)? living)|(what|which) "
        r"(country|city|town)( do)? (i|am i|i am)|"
        r"где я( нахожусь| сейчас|[.\?]?$)",
        re.IGNORECASE,
    ),
    "homeland": re.compile(
        r"(what is|what's|whats|tell me|you know|you remember|memorize|say) "
        r"my (home\s?land|mother\s?land|home\s?town|native\s?land|birth\s?place)|where (am i|i am) from|"
        r"откуда я( родом)[.\?]?$|где я родил(ась|ся)[.\?]?$",
        re.IGNORECASE,
    ),
}

BOT_DOESNT_KNOW_USER_INFO_RESPONSES = {
    "EN": {
        "name": "Sorry, we are still not familiar. What is your name?",
        "location": "Sorry, I don't have this information. But you can tell me. What is your location?",
        "homeland": "Sorry, I don't have this information. But you can tell me. Where are you from?",
    },
    "RU": {
        "name": "Извини, кажется, мы еще не знакомы. Как тебя зовут?",
        "location": "Извини, у меня нет такой информации, но ты можешь мне рассказать об этом. Где ты живешь сейчас?",
        "homeland": "Извини, у меня нет такой информации, но ты можешь мне рассказать об этом. Откуда ты родом?",
    },
}

TELL_USER_HIS_INFO_RESPONSE = {"EN": "Your {which_info} is {info}.", "RU": "Твое {which_info} - {info}."}
WHICH_INFO_RU_MAP = {
    "name": "имя",
    "location": "место проживания",
    "homeland": "место рождения",
}

ASK_USER_ABOUT_NAME_AGAIN_RESPONSE = {
    "EN": "My bad. What is your name again?",
    "RU": "Ой, извини. Как тебя зовут еще раз?",
}

AS_YOU_WISH_RESPONSE = {"EN": "As you wish.", "RU": "Как считаешь нужным."}
WHERE_DO_YOU_LIVE_NOW_RESPONSE = {"EN": "So, where do you live now?", "RU": "Так... А где ты сейчас живешь?"}
NEVER_HEARD_OF_NAME_RESPONSE = {"EN": "I've never heard about this name.", "RU": "Никогда не слышала такого имени."}
