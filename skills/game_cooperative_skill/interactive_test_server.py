import requests


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


def test_skill():
    url = "http://0.0.0.0:8068/respond"
    utterances = []
    while True:
        utterances = update_utterances(utterances=utterances, text_request=input("your request:"))
        human_utterances = [uttr for uttr in utterances if "hypotheses" in uttr]
        input_data = {"dialogs": [{"utterances": utterances, "human_utterances": human_utterances}]}
        response = requests.post(url, json=input_data).json()[0]
        utterances = update_utterances(utterances=utterances, response=response)
        text, confidence, attr = response
        # print(f"state:{attr['state']}")
        print(f"agent_intents:{attr['agent_intents']}")
        print(f"confidence:{confidence}")
        print(f"text:{text}")
    print("SUCCESS!")


if __name__ == "__main__":
    test_skill()
