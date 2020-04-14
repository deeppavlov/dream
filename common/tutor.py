from random import choice


tutor_phrases = [
    "Would you like to talk about something else? I can talk about movies, news,"
    " emotions, personality and other things. "
    "For example, just say \"tell me a funny story\" and I will happily tell you it!"
]


def get_tutor_phrase():
    return choice(tutor_phrases)
