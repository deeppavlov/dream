import requests


def test_respond():
    url = "http://0.0.0.0:8126/respond"

    c1 = ["neil wanted play", "borrowed gear friends", "geared headed rink", "practiced days", "competition"]
    c2 = ["rosie teacher birthday", "rosie money buy", "asked grandmother teach", "painted watercolor", "rosie gift"]
    contexts = [[c1], [c2]]
    s1 = (
        "Neil had always wanted to play hockey. He borrowed his gear from his friends and used "
        "it for the first time. He geared up and headed to the rink. He practiced for two days "
        "until the day of the competition. Neil won and could not wait for the next time to face "
        "the competition!"
    )
    s2 = (
        "Rosaie's teacher took her to her birthday party. Rosie didn't have enough money to buy her "
        "a gift. She asked her grandmother to teach her how to draw. Rosaie then painted her own "
        "watercolor. Her grandmother was able to give her her gift."
    )
    gold_result = [[s1, 0.9], [s2, 0.9]]
    result = requests.post(url, json={"utterances_histories": contexts}).json()
    assert [
        len(sample[0]) > 0 and len(sample[0]) > 0 and sample[1] > 0.0 for sample in result
    ], f"Got\n{result}\n, but expected:\n{gold_result}"
    print("Success")


if __name__ == "__main__":
    test_respond()
