import requests


def main():
    url = "http://0.0.0.0:8150/batch_model"

    input_data = {"sentences": ["Do you like ice cream?", "It's going to be sunny today",
                                 "I love dogs", "Do you want to know some interesting fact?", 
                                 "Wolves have small teeth"], 
                  "last_bot_utterances": [["I hate dogs", "The moon is a satellite of the earth"],
                                          [],
                                          ["I hate dogs", "Wolves have big teeth", "The moon is a satellite of the earth"],
                                          ["The moon is a satellite of the earth"],
                                          ["Wolves have big teeth", "The moon is a satellite of the earth"]]}
    desired_labels = ['neutral', 'neutral', 'contradiction', 'neutral', 'contradiction']

    result = requests.post(url, json=input_data).json()
    labels = [r['decision'] for r in result[0]['batch']]

    assert labels == desired_labels
    print("Successfully predicted contradiction!")


if __name__ == "__main__":
    main()
