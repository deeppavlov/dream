import requests

use_context = True


def main():
    url = "http://0.0.0.0:8113/respond"

    request_data = [
        {
            "active_skills": [["dff_friendship_skill", "dff_friendship_skill" "dff_music_skill"]],
            "cobot_topics": [["Phatic", "Phatic" "Phatic", "Music", "Phatic"]],
        }
    ]

    gold_results = [sorted(["dff_gossip_skill", "dff_movie_skill"])]

    count = 0
    for data, gold_result in zip(request_data, gold_results):
        result = requests.post(url, json=data).json()[0]
        if sorted(result) == gold_result:
            count += 1
        else:
            print(f"Got {result}, but expected: {gold_result}")

    assert count == len(request_data)
    print("Success")


if __name__ == "__main__":
    main()
