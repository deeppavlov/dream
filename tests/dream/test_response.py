import requests


if __name__ == '__main__':
    url = 'http://0.0.0.0:4242'
    user_id = 'test'
    result = requests.post(url, json={"user_id": user_id, "payload": "hey"}).json()
    print(result)
