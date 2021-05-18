import requests

use_context = True


def main():
    url = "http://0.0.0.0:8113/respond"

    request_data = [
        {
            "utterances_histories": [
                [
                    "i like to have conversation",
                    "Hi, this is an Alexa Prize Socialbot! I think we have not met yet. What name would you like "
                    "me to call you?",
                    "boss bitch",
                    "I'm so clever that sometimes I don't understand a single word of what i'm saying.",
                    "how is that",
                    "Hmm. If you would like to talk about something else just say, 'lets talk about something else'.",
                    "you pick the topic of conversation"
                ]
            ],
            "personality": [
                {}
            ],
            "num_ongoing_utt": [
                0
            ]
        }
    ]

    gold_results = [['dff_travel_skill', 'book_skill', 'dff_movie_skill']]

    count = 0
    for data, gold_result in zip(request_data, gold_results):
        result = requests.post(url, json=data).json()[0]
        if result == gold_result:
            count += 1
        else:
            print(f"Got {result}, but expected: {gold_result}")

    assert count == len(request_data)
    print("Success")


if __name__ == "__main__":
    main()
