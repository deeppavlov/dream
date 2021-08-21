# flake8: noqa
# %%
import pprint
from router import run_skills as skill
import random

SEED = 31415
random.seed(SEED)

# request_utters = ["t1", "top", "year", "ok", "talk about", "yes", "yes"]
# request_utters = ["t1", "top", "year", "ok", "talk about"]
request_utters = [
    "hi",
    "top of week",
    "yes",
    "go on",
    "move on",
    "top of last year",
    "yes",
    "talk",
    "yes",
    "ten",
    "next",
    "top of month",
    "no",
    "top",
]
true_response_utters = [
    "Love games. Got a list of the top released games, wanna discuss it?",
    " There were 3 newly released games highly rated in the last week. Do you want to learn more? ",
    "The game with the highest rating is Risk of Rain 2. It was released on August 11 2020. It's a combination of Action Shooter & Arcade. 48 percent of people marked Risk of Rain 2 as recommended.  If you want to discuss it in details say I want to talk about it.  Talking about it or going on? ",
    "The next game is Ghostrunner. It's Action. 33 percent of people marked Ghostrunner as skip.  Chatting about it or the next one? ",
    "The next game is UnderMine. It was released on August 06 2020. It's a combination of Action, Adventure RPG & Indie. 53 percent of people marked UnderMine as recommended.  These are all the games from the past week.  If you want to discuss it in details say I want to talk about it.  Otherwise we can always talk about other things.",
    " There were 20 newly released games highly rated in this year. Do you want to learn more? ",
    "The game with the highest rating is The Last of Us Part II. It was released on June 19 2020. It's a combination of Action Shooter & Adventure. 72 percent of people marked The Last of Us Part II as exceptional.  If you want to discuss it in details say I want to talk about it.  Discussing it or moving on? ",
    "Have you played it before? ",
    "So I suppose you liked The Last of Us Part II right? How would you rate the desire to play it again, from 1 to 10?",
    "You gave it a really high rating. Your rating is higher than one given by the rest of the players. Most of them rated it at 8.76 points. Well. I'd love to talk about other things but my developer forgot to add them to my memory banks. Please forgive him, he's young and very clever. For now can we please discuss the next game?",
    "The next game is DOOM Eternal. It was released on March 20 2020. It's a combination of  Action & Shooter. 59 percent of people marked DOOM Eternal as exceptional.  Discussing it or moving on? ",
    " There were 3 newly released games highly rated in the last month. Do you want to learn more? ",
    "You can always chat with me about other popular games. What do you want to talk about?",
    "Last time we had a conversation about the best games of the last month. For now, I can talk about the most popular games for this or last year, last month, or even the last week (hotties!). Which of these time periods is of interest for you?",
]

# true_response_utters = []
# request_utters = []

response_utters = []


def check(request_utters, response_utters, true_response_utters):
    for i, (req, ans, true_ans) in enumerate(zip(request_utters, response_utters, true_response_utters)):
        print(1)
        if ans != true_ans:
            print("=================================================")
            print(f"index = {i}: \nreq: {req} \nans : {ans} \nholy: {true_ans}")


state = {}
for i in request_utters:
    random.seed(SEED + len(response_utters))
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
    random.seed(SEED + len(response_utters))
    response, state = skill([req], state)
    print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    print("///////////////////////////////////////////////////////")
    print(f"test request: {req}")
    print(f"model {response['skill_name']}: {response['text']}")
    print("-------------------------------------------------------")
    response_utters.append(response["text"])
