import requests

from common.fact_random import load_fact_file


def main():
    url = "http://0.0.0.0:8119/respond"
    request_data = [["aardvark"]]

    possible_results = load_fact_file("./facts_for_animals.json")["aardvark"]

    result = requests.post(url, json=request_data).json()
    assert result[0][0]["fact"] in possible_results
    print("Success")


if __name__ == "__main__":
    main()
