import requests


def main():
    url = "http://0.0.0.0:8006/respond"
    input_data = {"sentences": ["i am watching a movie", "hey this is a white bear"]}
    result = requests.post(url, json=input_data)
    #assert result.json() == [["michal jordan"], ["a white bear"]]
    print(str(result.json() ))


if __name__ == "__main__":
    main()
