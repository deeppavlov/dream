import requests


def test_respond():
    url = "http://0.0.0.0:8127/respond"

    c1 = ["stars"]
    contexts = [[c1]]
    result = requests.post(url, json={"utterances_histories": contexts}).json()
    assert [
        len(sample[0]) > 0 and len(sample[0]) > 0 and sample[1] > 0.0 for sample in result
    ], f"Got\n{result}\n, something is wrong"
    print("Success")


if __name__ == "__main__":
    test_respond()
