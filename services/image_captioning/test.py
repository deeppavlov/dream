import requests


def test_respond():
    url = "http://0.0.0.0:8123/respond"

    img_path = ["/home/admin/test_img.jpg"]

    request_data = {"text": img_path}

    result = requests.post(url, json=request_data).json()

    print(result)


if __name__ == "__main__":
    test_respond()