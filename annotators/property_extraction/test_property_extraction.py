import requests
import time


def main():
    st_time = time.time()
    url = "http://0.0.0.0:8136/respond"

    request_data = [{"utterances": [["i live in moscow"]]}]
    gold_results = [[{"triplets": [{"object": "moscow", "relation": "live in general", "subject": "user"}]}]]

    count = 0
    for data, gold_result in zip(request_data, gold_results):
        result = requests.post(url, json=data).json()
        if result and result[0] == gold_result:
            count += 1
        else:
            print(f"Got {result}, but expected: {gold_result}")
        print(result)

    assert count == len(request_data)
    total_time = time.time() - st_time
    print("Success")
    print(f"property extraction exec time = {total_time:.3f}s")


if __name__ == "__main__":
    main()
