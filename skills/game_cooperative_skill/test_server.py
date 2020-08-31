# flake8: noqa
import requests
import difflib

SEED = 31415

true_requests = {}

false_requests = []
# Response struct
# [
#     {
#         "text": "t1.",
#         "hypotheses": [
#             {
#                 "skill_name": "game_cooperative_skill",
#                 "text": "b1.",
#                 "confidence": 1.0,
#                 "can_continue": "can",
#                 "state": {"1": 2},
#             }
#         ],
#     },
#     {"text": "b1.", "active_skill": "game_cooperative_skill", "confidence": 1.0},
#     {"text": "t2.", "hypotheses": []},
# ]


def update_utterances(utterances=[], response=None, text_request=""):
    if response:
        text, confidence, attr = response
        can_continue = attr["can_continue"]
        state = attr["state"]
        utterances[-1]["hypotheses"] = [
            {
                "skill_name": "game_cooperative_skill",
                "text": text,
                "confidence": confidence,
                "can_continue": can_continue,
                "state": state,
            }
        ]
        utterances += [
            {"text": text, "orig_text": text, "active_skill": "game_cooperative_skill", "confidence": confidence},
        ]
    if text_request:
        utterances += [
            {"text": text_request, "hypotheses": []},
        ]
    return utterances


request_utters = [
    "hi",
    "top of year",
    "yes",
    "go on",
    "move on",
    "top of year",
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
    "Love games. Got a list of the top released games, wanna discuss it? Say tell me about the best games",
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


def test_skill():
    url = "http://0.0.0.0:8068/respond"
    utterances = []
    warnings = 0
    for ind, (req_utter, true_resp_utter) in enumerate(zip(request_utters, true_response_utters)):
        utterances = update_utterances(utterances=utterances, text_request=req_utter)
        human_utterances = [uttr for uttr in utterances if "hypotheses" in uttr]
        input_data = {"dialogs": [{"utterances": utterances, "human_utterances": human_utterances}]}
        input_data["rand_seed"] = SEED + ind
        response = requests.post(url, json=input_data).json()[0]
        utterances = update_utterances(utterances=utterances, response=response)
        text, confidence, attr = response
        ratio = difflib.SequenceMatcher(None, true_resp_utter.split(), text.split()).ratio()
        if ratio != 1.0:
            print("----------------------------------------")
            print(f"req_utter = {req_utter}")
            print(f"true_resp_utter = {true_resp_utter}")
            print(f"cand_resp_utter = {text}")
            print(f"ratio = {ratio}")
            if ratio < 0.4:
                warnings += 1
        # print(difflib.SequenceMatcher(None, true_resp_utter.split(), text.split()).ratio())
    assert warnings == 0
    print("SUCCESS!")


if __name__ == "__main__":
    test_skill()
