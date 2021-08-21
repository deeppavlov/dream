import requests


dialog = [
    "hi",
    "hi",
    "how are you?",
    "I'm fine. how are you?",
    "Good. What do you do?",
    "I response test questions",
]

checked_cand_nums = [3, 3, 3, 3, 3]


def history_gen(dialog):
    for i in range(1, len(dialog) + 1):
        history = dialog[:i]
        yield history


def test_skill():
    url = "http://localhost:8029/convert_reddit"
    for utterances, checked_cand_num in zip(history_gen(dialog), checked_cand_nums):
        res = requests.post(
            url,
            json={"utterances_histories": [utterances], "approximate_confidence_is_enabled": False},
        )
        assert str(res.status_code) == "200"
        print(res.json())
        # assert len([i for i in res.json()[0][0] if i]) == checked_cand_num
    print("SUCCESS!")


if __name__ == "__main__":
    test_skill()
