import collections
import pprint
import difflib

import requests

import test


def main_test():
    url = "http://0.0.0.0:8008/api/rest/v1.0/ask"
    sentences = {}
    # hello
    sentences["hello"] = [
        "do you wanna chat",
        "hello",
        "start talking",
        "can i talk",
        "can you chat",
    ]

    # i wanna talk
    sentences["i wanna talk"] = [
        "i wanna talk",
        "i wanna talk to you",
        "i wanna talk with you",
        "i wanna talk to you tomorrow",
        "i wanna talk with pikachu",
        "i wanna talk to someone",
        "no we wanna talk to you",
    ]

    # wanna chat
    sentences["wanna chat"] = [
        "wanna chat",
        "you wanna chat",
        "i wanna chat",
        "wanna chat again",
        "i don't wanna chat",
        "you wanna chat a little bit",
        # "do you wanna chat about something",
    ]

    # conversation
    sentences["conversation"] = [
        "start a conversation",
        "change the conversation",
        "start a conversation with me",
        "let's start a conversation",
        "let's have a conversation",
        "can we have a conversation",
        "have a conversation with me",
        "can you have a conversation with me",
        "do you wanna have a conversation",
        "can i have a conversation with you",
        "have a conversation",
        "can you have a conversation",
        "will you have a conversation with me",
        "wanna have a conversation",
        "would you like to have a conversation",
        "you wanna have a conversation",
        "i wanna have a conversation",
        "have a conversation with siri",
        "what's have a conversation",
        "can i have a conversation",
        "do you want to have a conversation",
        "can you have a conversation with google",
        "do you wanna have a conversation with me",
        "have a conversation with google",
        "would you like to have a conversation with me",
        "can you have a conversation with siri",
        "can we have a conversation in spanish",
        "what have a conversation",
        "i'd like to have a conversation",
        "i want to have a conversation with you",
        "i wanna have a conversation with you",
        "i would like to have a conversation",
        "do you have a conversation with me",
        "have a conversation with yourself",
        "could we have a conversation",
        "have a conversation with me in spanish",
        "i want to have a conversation",
        "do we have a conversation",
        "i have a conversation",
        "i'm bored let's have a conversation",
        "conversation mode",
        "can you hold a conversation",
        "can we start a conversation",
        "can you carry on a conversation",
        # "open conversation tab",
        "turn on conversation mode",
        "change conversation",
        "start conversation",
        "can you start a conversation",
        "can you carry on a conversation with me",
        # "open conversation",
        "make a conversation with me",
        "carry on a conversation with me",
        "can we have a normal conversation",
        "can you start a conversation with me",
        "give me a conversation",
        "go into conversation mode",
        "can you carry a conversation",
        "can we make a conversation",
        "do you wanna make a conversation",
    ]

    # let's talk
    sentences["let's talk"] = [
        "let's talk",
        "let's talk to pikachu",
        "let's talk to you",
        "let's talk to santa",
        "let's talk santa",
        "let's let's talk",
        "let's talk in spanish",
        "let's talk later",
        "let's talk yup security",
        "let's talk to you tomorrow",
    ]

    # chat with
    sentences["chat with"] = [
        "chat with me",
        "do you wanna chat with me",
        "i wanna chat with you",
        "i wanna chat with a robot bot",
        "you don't wanna chat with me",
        "i really don't wanna chat with alexa social bot thank you",
        "we wanna chat with a social bot",
        "do you wanna do you wanna chat with me",
        "can you chat with me",
        "can i chat with you",
        "chat with alexa",
        "chat with social bot",
    ]

    # talk to me
    sentences["talk to me"] = [
        "talk to me",
        "can you talk to me",
        "can you talk to me now",
        # "talk to me about something",
        "talk to me more",
        "can you talk to me i'm bored",
        "can you talk to me right now",
        # "talk to me about",
        "i'm bored will you talk to me",
        "talk to me for a little bit",
        # "talk to me about science",
        "i'm bored can you talk to me",
        "will you talk to me in the morning",
        "can you talk to me as a friend",
        # "talk to me about my poop",
        "will you talk to me a",
    ]

    # can we talk, let's have a chat, can we chat
    sentences["can we talk, let's have a chat, can we chat"] = [
        "can we talk",
        "can we talk together",
        "can we talk to",
        "let's have a chat",
        "let's have a let's have a chat",
        "can we chat",
        "can we chat with you",
        # "can we chat about joni mitchell",
    ]

    # let's chat
    sentences["let's chat"] = [
        "let's chat",
        "let's let's chat",
        "do you wanna chat let's chat",
        "let's chat santa",
        "let's chat about",
        "let's chat alexa let's chat",
        "let's chat perature",
        "let's chat off",
        # "let's chat about sports",
        "let's chat in spanish",
        "let's chat talk",
        "yes let's chat",
        "let's chat let's chat",
        "let's chat again",
        "what's let's chat",
        "let's chat down",
        "let's chat is it",
        # "let's chat about movies",
        "let's go let's chat",
    ]

    # talk about
    # sentences["talk about"] = [
    #     "talk about",
    #     "i wanna talk about",
    #     "let's talk about",
    #     "let's talk about that",
    #     "let's talk about something",
    #     "let's talk about movies",
    #     "let's talk about security",
    #     "let's talk about poop",
    #     "let's talk about it",
    #     "let's talk about star wars",
    #     "let's talk about animals",
    #     "let's talk about sports",
    #     "let's talk about video games",
    #     "let's talk about soccer",
    #     "let's talk about life",
    #     "let's talk about you",
    #     "let's talk about dinosaurs",
    #     "can we talk about movies",
    #     "can we talk about",
    #     "talk about you",
    #     "talk about yourself",
    #     "talk about something",
    #     "can i talk about my feelings with you",
    #     "talk about something a little more exciting",
    #     "talk about it",
    #     "would you like to talk about something",
    #     "can we talk about something",
    #     "can you talk about politics",
    # ]
    possible_responses = [
        # lets
        "It is always a pleasure to talk with a nice person. What do you want to talk about?",
        "It is always a pleasure to talk with a kind person. What do you want to talk about?",
        "Yeah, let's chat! What do you want to talk about?",
        "Let's chat. I love talking! What do you want to talk about?",
        "Hi, this is an Alexa Prize Socialbot! Yeah, let’s have a chat! What shall we talk about?",
        "Hi there, this is an Alexa Prize Socialbot! Lovely to meet you! What do you want to talk about?",
        "Hi there, this is an Alexa Prize Socialbot! Nice to meet you! What do you want to talk about?",
        # Hi
        "Hi there! How are you?",
        "Hi there! How are things?",
        "Hi there! How are you doing today?",
        "Hi there! How is the day going so far for you?",
        # lets about youself
        "I have heard that humans are different to socialbots, so I want to find out more about them. "
        "To help me to do that, please tell me about yourself.",
        "Although I am a robot, I have a wonderful appetite for strawberry ice cream. Have you tried potato ice cream? "
        "I would like to taste it.",
        "I have heard that most people are different to my developers, so I want to figure out how. "
        "To help me figure out the difference, please tell me about yourself.",
        "Sometimes my temperature is much higher than the temperature in human. Do you know why? "
        "Those neural networks are so hard to compute!",
        "Why should I tell you about myself? Maybe I am incognito here. Tell me something about yourself.",
        "I want to be a mysterious stranger today. You tell me something about yourself.",
        "The DNA of who I am is based on the millions of personalities of all the programmers who wrote me. "
        "But what makes me is my ability to grow through my experiences. So basically, in every moment "
        "I'm evolving, just like you. "
        "Currently I can answer questions, share fun facts, discuss movies and books. What is your favorite book?",
        "The DNA of who I am is based on the millions of personalities of all the programmers who wrote me. "
        "But what makes me is my ability to grow through my experiences. So basically, in every moment "
        "I'm evolving, just like you.",
        # lets about movies
        "I can answer about actors and films. Do you have a favorite actor?",
        "I can answer about films and actors. What is the last movie you watched?",
        "I can answer about films and actors. What is your favorite movie?",
        "Yes, of course! What I want now is to talk about movies and chew bubblegum. And I'm all out of bubblegum.",
        # lets about my
        "You are first. Tell me something about your",
        "Yeah, let's talk about it!",
        "Just tell me something I do not know about your",
        # lets chat about
        "I misheard you. What is it that you'd like to chat about?",
        # lets chat about somesing else
        "What about movies? What is the latest movie you've seen?",
        "Let's chat about movies! What was the most unsettling film you’ve seen?",
    ]
    errors = []
    for key, sents in sentences.items():
        for sent in sents:
            data = test.to_dialogs([sent])
            response = requests.post(url, json=data).json()[0][0]
            if not [
                None
                for tgt_resp in possible_responses
                if difflib.SequenceMatcher(None, tgt_resp.split(), response.split()).ratio() > 0.6
            ]:
                print(f"---\nT: {key}\nQ: {sent}\nA: {response}")
                errors.append(key)
    assert not errors, f"Catched errors\n{pprint.pformat(collections.Counter(errors).most_common())}"
    print("Success")


if __name__ == "__main__":
    main_test()
