import re

OPINION_REQUESTS_ABOUT_MUSIC = ["What kind of music do you like?",
                                "What kind of music do you listen to to cheer you up?",
                                "What kind of music do you usually listen to?",
                                "Who is your favorite singer?",
                                "What song do you like to sing?",
                                "What is your favorite album?",
                                "Who do you think is the best band ever?"
                                ]

MUSIC_COMPILED_PATTERN = re.compile(r"(music|song)", re.IGNORECASE)


def skill_trigger_phrases():
    return OPINION_REQUESTS_ABOUT_MUSIC
