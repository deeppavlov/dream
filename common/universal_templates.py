from random import choice


# https://www.englishclub.com/vocabulary/fl-asking-for-opinions.htm
UNIVERSAL_OPINION_REQUESTS = [
    "This is interesting, isn't it?",
    "What do you reckon?",
    "What do you think?",
]

NP_OPINION_REQUESTS = [
    "What do you think about NP?",
    "What are your views on NP?",
    "What are your thoughts on NP?",
    "How do you feel about NP?",
    # "I wonder if you like NP.",
    # "Can you tell me do you like NP?",
    # "Do you think you like NP?",
    "I imagine you will have strong opinion on NP.",
    "What reaction do you have to NP?",
    "What's your take on NP?",
    "I'd be very interested to hear your views on NP.",
    "Do you have any particular views on NP?",
    "Any thoughts on NP?",
    "Do you have any thoughts on NP?",
    "What are your first thoughts on NP?",
    "What is your position on NP?",
    "What would you say if I ask your opinion on NP?",
    "I'd like to hear your opinion on NP."
]


def nounphrases_questions(nounphrase=None):
    if nounphrase and len(nounphrase) > 0:
        question = choice(NP_OPINION_REQUESTS + UNIVERSAL_OPINION_REQUESTS).replace("NP", nounphrase)
    else:
        question = choice(UNIVERSAL_OPINION_REQUESTS)
    return question
