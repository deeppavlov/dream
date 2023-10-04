import requests


def test_respond():
    url = "http://0.0.0.0:8069/respond"

    image_paths = ["https://s0.rbk.ru/v6_top_pics/media/img/7/26/346832135841267.jpg"]
    sentences = ["What is the make of the car?"]
    request_data = {"image_paths": image_paths, "sentences": sentences}
    result = requests.post(url, json=request_data).json()
    print(result)

    obligatory_word = "SUV"
    assert obligatory_word in result[0], f"Expected the word '{obligatory_word}' to present in caption"
    print("\n", "Success!!!")


if __name__ == "__main__":
    test_respond()
