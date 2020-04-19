# flake8: noqa
import requests
import difflib


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
            {"text": text, "active_skill": "game_cooperative_skill", "confidence": confidence},
        ]
    if text_request:
        utterances += [
            {"text": text_request, "hypotheses": []},
        ]
    return utterances


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


def test_skill():
    url = "http://0.0.0.0:8068/respond"
    utterances = []
    warnings = 0
    for ind, (req_utter, true_resp_utter) in enumerate(zip(request_utters, true_response_utters)):
        utterances = update_utterances(utterances=utterances, text_request=req_utter)
        human_utterances = [uttr for uttr in utterances if "hypotheses" in uttr]
        input_data = {"dialogs": [{"utterances": utterances, "human_utterances": human_utterances}]}
        if ind == 0:
            input_data["rand_seed"] = 31415
        response = requests.post(url, json=input_data).json()[0]
        utterances = update_utterances(utterances=utterances, response=response)
        text, confidence, attr = response
        if difflib.SequenceMatcher(None, true_resp_utter.split(), text.split()).ratio() != 1.0:
            print("----------------------------------------")
            print(f"req_utter = {req_utter}")
            print(f"true_resp_utter = {true_resp_utter}")
            print(f"cand_resp_utter = {text}")
            warnings += 1
        print(difflib.SequenceMatcher(None, true_resp_utter.split(), text.split()).ratio())
    assert warnings == 0
    print("SUCCESS!")


if __name__ == "__main__":
    test_skill()
