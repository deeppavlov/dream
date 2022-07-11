import requests


def main():
    url = "http://0.0.0.0:8007/respond"
    input_data = {"sentences": ["i eat stars for breakfast and moon for dinner", "i am a dog, but mostly a cat"]}
    result = requests.post(url, json=input_data)
    assert result.json() == [["breakfast", "moon", "dinner"], ["dog", "mostly", "cat"]]
    print("Success!")


if __name__ == "__main__":
    main()
