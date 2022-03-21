import os
import requests


SERVICE_PORT = int(os.getenv("SERVICE_PORT"))


def main():
    url = f"http://0.0.0.0:{SERVICE_PORT}/respond"
    input_data = {"sentences": ["i like michal jordan", "hey this is a white bear"]}
    result = requests.post(url, json=input_data)
    assert result.json() == [["michal jordan"], ["a white bear"]]
    print("Success!")


if __name__ == "__main__":
    main()
