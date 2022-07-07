import requests


def test_respond():
    url = "http://0.0.0.0:8127/respond"

    c1 = ['stars']
    contexts = [[c1]]
    s1 = "Ok, Let me share a story about stars. I love stars, and when I hear about something that made " \
         "a star explode i feel like a child that just witnessed the birth of a god. " \
         "Like when I watch the star explosion on the Discovery channel, i am awestruck at the phenomenon " \
         "that these things cause. I know the famous one where the star is consumed by a black hole and " \
         "everything around it disappears. In the end, however, it is the little things that make the " \
         "universe so special."
    gold_result = [[s1, 1.0]]
    result = requests.post(url, json={"utterances_histories": contexts}).json()
    assert [
        len(sample[0]) > 0 and len(sample[0]) > 0 and sample[1] > 0.0
        for sample in result], f"Got\n{result}\n, but expected:\n{gold_result}"
    print("Success")


if __name__ == "__main__":
    test_respond()
