# flake8: noqa
# %%
import pprint
from router import run_skills as skill
import random

random.seed(31415)

# request_utters = ["t1", "top", "year", "ok", "talk about", "yes", "yes"]
# request_utters = ["t1", "top", "year", "ok", "talk about"]
request_utters = []
request_utters = [
    "hello",
    "top",
    "week",
    "yes",
    "ok",
    "top of month",
    "yes",
    "talk",
    "yes",
    "yes",
    "stop",
    "top of year",
    "yes",
    "yes",
    "say",
    "yes",
    "yes",
    "no",
    "awful",
    "next",
    "next",
    "next",
    "stop",
    "top",
    "no",
    "stop",
    "top of last month",
    "yes",
    "tell me about top of last year",
    "stop",
    "i wanna",
]

true_response_utters = [
    "I like to talk about games. Got a list of the top released games, wanna discuss it? Say tell me about the best games",
    "I can tell you about popular games. For now, I can talk about the most popular games for this or last year , last month, or even the last week (hotties!). Which of these time periods is of interest for you?",
    " There was 1 newly released game highly rated in the last week. Do you want to learn more? ",
    "The game with the highest rating is Final Fantasy VII Remake. It was released on 10 April 2020. It's a combination of Action Adventure & RPG. 90 percent of people marked Final Fantasy VII Remake as exceptional. These are all the games from the past week. Let's talk about something else. ",
    "I like to talk about games. Got a list of the top released games, wanna discuss it? Say tell me about the best games",
    " There was 1 newly released game highly rated in the last month. Do you want to learn more? ",
    "The game with the highest rating is Final Fantasy VII Remake. It was released on 10 April 2020. It's a combination of Action Adventure & RPG. 90 percent of people marked Final Fantasy VII Remake as exceptional. These are all the games from the past month. Let's talk about something else. ",
    "Do you want to talk in more detail about the game called Final Fantasy VII Remake?",
    "Have you played it before? ",
    "So I suppose you liked Final Fantasy VII Remake right? How would you rate the desire to play it again, from 1 to 10?",
    "OK, I won’t continue, but if you want to talk about the best games, Say tell me about the coolest games",
    " There were 18 newly released games highly rated in this year. Do you want to learn more? ",
    "The game with the highest rating is Dota Underlords. It was released on 25 February 2020. It's a combination of Strategy Board Games & Casual. 44 percent of people marked Dota Underlords as recommended. If you want to discuss it in details say I want to talk about it. ",
    "The next game is Black Mesa. It was released on 06 March 2020. It's a combination of  Shooter & Indie. 46 percent of people marked Black Mesa as exceptional. If you want to discuss it in details say I want to talk about it. ",
    "Do you want to talk in more detail about the game called Black Mesa?",
    "Have you played it before? ",
    "So I suppose you liked Black Mesa right? How would you rate the desire to play it again, from 1 to 10?",
    "I didn't get what you've just said. I asked what rating would you give Black Mesa. For example, you can say: one or ten  or any number from 1 to 10. Or do you want to stop for now?",
    "You gave it a super low rating. Your rating is way lower than one given by the rest of the players. Most of them rated it at 8.6 points. Well. I'd love to talk about other things but my developer forgot to add them to my memory banks. Please forgive him, he's young and very clever. For now can we please discuss the next game?",
    "The next game is Besiege. It was released on 18 February 2020. It's a combination of Strategy Simulation & Indie. 66 percent of people marked Besiege as recommended. If you want to discuss it in details say I want to talk about it. ",
    "The next game is DOOM Eternal. It was released on 20 March 2020. It's a combination of  Action & Shooter. 58 percent of people marked DOOM Eternal as exceptional. If you want to discuss it in details say I want to talk about it. ",
    "The next game is Ori and the Will of the Wisps. It was released on 11 March 2020. It's a combination of  Adventure & Platformer. 67 percent of people marked Ori and the Will of the Wisps as exceptional. If you want to discuss it in details say I want to talk about it. ",
    "OK, I won’t continue, but if you want to talk about the best games, Say tell me about the coolest games",
    "Last time we talked about the best games of this year. For now, I can talk about the most popular games for this or last year , last month, or even the last week (hotties!). Which of these time periods is of interest for you?",
    "You can always talk to me about other popular games. What do you want to talk about?",
    "OK, I won’t continue, but if you want to talk about the best games, Say tell me about the coolest games",
    " There was 1 newly released game highly rated in the last month. Do you want to learn more? ",
    "The game with the highest rating is Final Fantasy VII Remake. It was released on 10 April 2020. It's a combination of Action Adventure & RPG. 90 percent of people marked Final Fantasy VII Remake as exceptional. These are all the games from the past month. Let's talk about something else. ",
    " There were 20 newly released games highly rated in the last year. Do you want to learn more? ",
    "OK, I won’t continue, but if you want to talk about the best games, Say tell me about the coolest games",
    "Last time we talked about the best games of last year. For now, I can talk about the most popular games for this or last year , last month, or even the last week (hotties!). Which of these time periods is of interest for you?",
]

response_utters = []


def check(request_utters, response_utters, true_response_utters):
    for i, (req, ans, true_ans) in enumerate(zip(request_utters, response_utters, true_response_utters)):
        if ans != true_ans:
            print("=================================================")
            print(f"index = {i}: \nreq: {req} \nans : {ans} \nholy: {true_ans}")


state = {}
for i in request_utters:
    response, state = skill([i], state)
    # print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    # print("///////////////////////////////////////////////////////")
    # print(f"test request: {i}")
    # print(f"model {response['skill_name']}: {response['text']}")
    # print("-------------------------------------------------------")
    response_utters.append(response["text"])

check(request_utters, response_utters, true_response_utters)

while True:
    req = input("test request: ")
    if "#" in req:
        if req == "#req":
            print(request_utters)
        elif req == "#ans":
            print(response_utters)
        elif req == "#dif":
            check(request_utters, response_utters, true_response_utters)
        continue
    request_utters.append(req)
    response, state = skill([req], state)
    print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    print("///////////////////////////////////////////////////////")
    print(f"test request: {req}")
    print(f"model {response['skill_name']}: {response['text']}")
    print("-------------------------------------------------------")
    response_utters.append(response["text"])
