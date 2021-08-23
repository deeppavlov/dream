import requests


def main():
    url = 'http://0.0.0.0:8116/respond'
    request_data = [{"wikihow_titles": [["Photograph-Pets"]]}]
    count = 0
    for data in request_data:
        res = requests.post(url, json=data, timeout=1.0).json()
        if res and res[0]["wikihow_content"]:
            count += 1
        else:
            print("Not found content")
    assert count == len(request_data)
    print('Success')


if __name__ == '__main__':
    main()
