import requests


def main():
    url = "http://0.0.0.0:8136/respond"

    request_data = [{"utterances": [["i live in moscow"]]}]
    gold_results = [[{"triplet": {"object": "moscow", "relation": "live in citystatecountry", "subject": "user"}}]]

    count = 0
    for data, gold_result in zip(request_data, gold_results):
        result = requests.post(url, json=data).json()
        if result and result[0] == gold_result:
            count += 1
        else:
            print(f"Got {result}, but expected: {gold_result}")
        print(result)

    assert count == len(request_data)
    print("Success")


if __name__ == "__main__":
    main()
