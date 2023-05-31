import requests


def main():
    url = "http://0.0.0.0:8150/batch_model"

    input_data = {
        "sentences": [
            "Do you like ice cream?",
            "It's going to be sunny today",
            "I love dogs",
            "Do you want to know some interesting fact?",
            "Wolves have small teeth",
        ],
        "last_bot_utterances": [
            ["I hate dogs", "The moon is a satellite of the earth"],
            [],
            [
                "I hate dogs",
                "Wolves have big teeth",
                "The moon is a satellite of the earth",
            ],
            ["The moon is a satellite of the earth"],
            ["Wolves have big teeth", "The moon is a satellite of the earth"],
        ],
    }
    desired_output = [
        {
            "decision": "neutral",
            "entailment": 0.0019908840768039227,
            "neutral": 0.7070657014846802,
            "contradiction": 0.2909433841705322,
        },
        {
            "decision": "neutral",
            "entailment": 0.0,
            "neutral": 1.0,
            "contradiction": 0.0,
        },
        {
            "decision": "contradiction",
            "entailment": 2.6359959974797675e-06,
            "neutral": 0.0002536950050853193,
            "contradiction": 0.999743640422821,
        },
        {
            "decision": "neutral",
            "entailment": 0.014720427803695202,
            "neutral": 0.9783505797386169,
            "contradiction": 0.0069289617240428925,
        },
        {
            "decision": "contradiction",
            "entailment": 0.0019739873241633177,
            "neutral": 0.0290225762873888,
            "contradiction": 0.9690034985542297,
        },
    ]

    result = requests.post(url, json=input_data).json()

    for rez in desired_output:
        for k, v in rez.items():
            if type(v) == float:
                rez[k] = round(v, 2)

    for rez in result[0]["batch"]:
        for k, v in rez.items():
            if type(v) == float:
                rez[k] = round(v, 2)
    assert result[0]["batch"] == desired_output
    print("Successfully predicted contradiction!")


if __name__ == "__main__":
    main()
