import requests


def test():
    response = requests.post("http://0.0.0.0:8026/model", json={"personality": ["Hello world"]})
    assert response.status_code == 200
    assert response.json() == [{"EXT": 0, "NEU": 1, "AGR": 1, "CON": 0, "OPN": 1}]
    print("SUCCESS")


if __name__ == "__main__":
    test()
