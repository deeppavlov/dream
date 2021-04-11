import re

OPINION_REQUESTS_ABOUT_MUSIC = ["What music do you like?",
                                "Do you like listening to music?",
                                "What do you listen to?",
                                "Who is your favorite artist?",
                                "What is your favorite song?",
                                "What is your favorite album?",
                                "Do you have a favorite artist?"
                                ]

MUSIC_COMPILED_PATTERN = re.compile(r"(music|song)", re.IGNORECASE)


def skill_trigger_phrases():
    return OPINION_REQUESTS_ABOUT_MUSIC
