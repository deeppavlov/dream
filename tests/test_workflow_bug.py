import requests


def main():
    url = 'http://0.0.0.0:4242'
    response = requests.post(url, json={"user_id": "test", "payload": "yes"}).json()
    assert "response" in response.keys()
    response = requests.post(url, json={"user_id": "test", "payload": ""}).json()
    assert "response" in response.keys()
    response = requests.post(url, json={"user_id": "test", "payload": "yes"}).json()
    assert "response" in response.keys()

    print("SUCCESS test workflow bug")


if __name__ == "__main__":
    main()
