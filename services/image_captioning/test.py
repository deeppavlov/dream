import requests


def test_respond():
    url = "http://0.0.0.0:8123/respond"

    image_paths = ["example.jpg"]

    request_data = {"image_paths": image_paths}
    result = requests.post(url, json=request_data).json()
    obligatory_word = "bird"

    assert obligatory_word in result[0]["caption"], f"Expected the word '{obligatory_word}' to present in caption"
    print("\n", "Success!!!")


if __name__ == "__main__":
    test_respond()
