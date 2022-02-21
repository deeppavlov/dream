import json
import requests


URL = "http://0.0.0.0:8121/respond"

utterances = [
    [
        "Yeah I think the original is going to be the best. Did you know that Stephen King actually thinks that the "
        "movie Bambi should be a horror movie?",
        "He was traumatized as a child. That movie did have death. so it could be scary. Anyway. "
        "he turned his trauma into a career.",
        "Well that's really good for him! Do you think that horror movies actually burn almost 200 calories per movie? "
        "If so I should watch more to lose weight LOL",
    ]
]

with open("test_midas_distributions.json", "r") as f:
    midas_distributions = json.load(f)

gold = [
    {
        "appreciation": 0.021464481396361437,
        "command": 0.014961019602555794,
        "comment": 0.13228056116328482,
        "complaint": 0.01237072553737834,
        "dev_command": 0.00013864256480218282,
        "neg_answer": 0.0653513829767115,
        "open_question_factual": 0.013992507813657644,
        "open_question_opinion": 0.015530223705766988,
        "opinion": 0.25595647566650004,
        "other_answers": 0.013316840317939735,
        "pos_answer": 0.11561513926623856,
        "statement": 0.27141031284547645,
        "yes_no_question": 0.06761168714332645,
    }
]

if __name__ == "__main__":

    requested_data = {"utterances": utterances, "midas_distributions": midas_distributions}
    result = requests.post(URL, json=requested_data).json()
    assert result == gold
    print("Success")
