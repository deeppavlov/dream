import requests


def test_respond():
    url = "http://0.0.0.0:8123/respond"

    img_path = ["example.jpg"]

    request_data = {"text": img_path}
    result = requests.post(url, json=request_data).json()
    caption = result["caption"][0][0]["caption"]
    print(caption)
    obligatory_word = "bird"

    assert obligatory_word in caption, f"Expected the word '{obligatory_word}' to present in caption"
    print("\n", "Success!!!")


if __name__ == "__main__":
    test_respond()
