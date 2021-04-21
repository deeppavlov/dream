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


def update_utterances(utterances=None, response=None, text_request=""):
    utterances = [] if utterances is None else utterances
    if response:
        text, confidence, _, _, attr = response
        can_continue = attr.get("can_continue", "")
        utterances[-1]["hypotheses"] = [
            {
                "skill_name": "game_cooperative_skill",
                "text": text,
                "confidence": confidence,
                "can_continue": can_continue,
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
    "yeah sure",
    "top of last year",
    "go on",
    "move on",
    "top of last year",
    "yeah sure",
    "talk",
    "yeah sure",
    "ten",
    "next",
]
true_response_utters = [
    "So, well, one of my hobbies is keeping fresh stats about the top video games. Wanna dig into it?",
    "I can tell you a few things about popular games. For now, I can talk about the most popular games for this or last year, last month, or even the last week (hotties!). Which of these time periods is of interest for you?",
    "There were 20 newly released games highly rated in the last year. Do you want to learn more? ",
    "The game with the highest rating is Cyberpunk 2077. It was released on December 10 2020. It's a combination of  Action & RPG. 58 percent of people marked Cyberpunk 2077 as exceptional.  If you want to discuss it in details say I want to talk about it.  Chatting about it or the next one? ",
    "The next game is Fall Guys: Ultimate Knockout. It was released on August 04 2020. It's a combination of Action, Sports, Casual Massively Multiplayer & Indie. 60 percent of people marked Fall Guys: Ultimate Knockout as recommended.  Discussing it or moving on? ",
    "There were 20 newly released games highly rated in the last year. Do you want to learn more? ",
    "The game with the highest rating is Cyberpunk 2077. It was released on December 10 2020. It's a combination of  Action & RPG. 58 percent of people marked Cyberpunk 2077 as exceptional.  If you want to discuss it in details say I want to talk about it.  Discussing it or moving on? ",
    "Have you played it before? ",
    "So I suppose you liked Cyberpunk 2077 right? How would you rate the desire to play it again, from 1 to 10?",
    "You gave it a really high rating. Your rating is higher than one given by the rest of the players. Most of them rated it at 8.4 points. Well. I'd love to talk about other things but my developer forgot to add them to my memory banks. Please forgive him, he's young and very clever. For now can we please discuss the next game?",
    "The next game is Fall Guys: Ultimate Knockout. It was released on August 04 2020. It's a combination of Action, Sports, Casual Massively Multiplayer & Indie. 60 percent of people marked Fall Guys: Ultimate Knockout as recommended.  Discussing it or moving on? ",
]


def test_skill():
    url = "http://0.0.0.0:8068/respond"
    utterances = []
    warnings = 0
    human_attr = {}
    bot_attr = {}

    for ind, (req_utter, true_resp_utter) in enumerate(zip(request_utters, true_response_utters)):
        utterances = update_utterances(utterances=utterances, text_request=req_utter)
        human_utterances = [uttr for uttr in utterances if "hypotheses" in uttr]
        bot_utterances = [uttr for uttr in utterances if "hypotheses" not in uttr]
        input_data = {
            "dialogs": [
                {
                    "utterances": utterances,
                    "human_utterances": human_utterances,
                    "bot_utterances": bot_utterances,
                    "human": {"attributes": human_attr},
                    "bot": {"attributes": bot_attr},
                }
            ]
        }
        input_data["rand_seed"] = SEED + ind
        response = requests.post(url, json=input_data).json()[0]
        utterances = update_utterances(utterances=utterances, response=response)
        text, confidence, human_attr, bot_attr, attr = response
        ratio = difflib.SequenceMatcher(None, true_resp_utter.split(), text.split()).ratio()

        print("----------------------------------------")
        print(f"req_utter = {req_utter}")
        print(f"true_resp_utter = {true_resp_utter}")
        print(f"cand_resp_utter = {text}")
        print(f"ratio = {ratio}")

        if ratio < 0.35:
            warnings += 1
            print(f"warning={warnings}")
        # print(difflib.SequenceMatcher(None, true_resp_utter.split(), text.split()).ratio())
    assert warnings == 0
    print("SUCCESS!")


if __name__ == "__main__":
    test_skill()
