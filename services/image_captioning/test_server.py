import requests

def test_respond():
    url = "http://0.0.0.0:8123/respond"

    path = ["example.jpg"]
    request_data = {"text": path}
    response = requests.post(url, json=request_data)
    assert response.status_code == 200
    print("Test respond passed")

def test_incorrect_respond():
    url = "http://0.0.0.0:8123/respond"

    path = ["this_image_does_not_exist.jpg"]
    request_data = {"text": path}
    response = requests.post(url, json=request_data)
    assert response.status_code != 200
    print("Test incorrect respond passed")


if __name__ == "__main__":
    test_respond()
    test_incorrect_respond()
