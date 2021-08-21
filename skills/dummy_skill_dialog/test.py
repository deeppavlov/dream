import requests
import json
from copy import deepcopy


def get_input_json(fname):
    with open(fname, "r") as f:
        res = json.load(f)
    return {"dialogs": res}


def slice_(input_data, i):
    tmp_data = deepcopy(input_data)
    tmp_data["dialogs"][0]["utterances"] = input_data["dialogs"][0]["utterances"][:i]
    tmp_data["dialogs"][0]["human_utterances"] = []
    tmp_data["dialogs"][0]["bot_utterances"] = []

    for uttr in tmp_data["dialogs"][0]["utterances"]:
        if uttr["user"]["user_type"] == "human":
            tmp_data["dialogs"][0]["human_utterances"].append(deepcopy(uttr))
        else:
            tmp_data["dialogs"][0]["bot_utterances"].append(deepcopy(uttr))

    return tmp_data


def main_test():
    url = "http://0.0.0.0:8052/respond"
    input_data = get_input_json("test_dialog.json")
    sliced_data = [slice_(input_data, i) for i in range(3, 21, 2)]
    responses = [requests.post(url, json=tmp).json()[0][0] for tmp in sliced_data]
    gold_phrases = [
        "i mainly like marvel. apparently they published a generic comic book so they could trade mark "
        "super-hero and super-villian.",
        "i know right, it's strange that was even an option. dc actually stands for detective comics. "
        "i didn't know that.",
        "they said to make the name redundant. so weird. " "i thought stan lee was an amazing human, did you like him?",
        "i would have liked to as well. "
        "i never thought about when the marvel cinematic universe took place,"
        " it takes place in earth-199999. not sure what that means "
        "but it's a multiverse and different from the original earth-616.",
        "oh that makes sense. have you ever been to the michigan state library? "
        "it has the largest comic book collection in the world.",
        "wow, that is cool! i wonder how many actually exist.",
        "i never really got into the batman comics but i do love the movies.",
        "i enjoyed the animated series as well as some of the new ones, " "my kids and i enjoy teen titans go!",
        "i heard about titans not streaming on dc universe's streaming service but haven't watched it. "
        "have you seen it yet?",
        "oh well, maybe it'll be good, if not kids still have teen titans! haha, well it was nice talking "
        "to you, i've gotta run now, bye!",
    ]

    for response, gold_phrase in zip(responses, gold_phrases):
        assert response == gold_phrase, print(f"Expect: {gold_phrase}. Got: {response}.")


if __name__ == "__main__":
    main_test()
