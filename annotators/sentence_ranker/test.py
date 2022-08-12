import requests


def main():
    url = "http://0.0.0.0:8124/batch_model"
    request_data = {
        "hypotheses": [
            "that a great name for a cat",
            "i don't want to talk about politics",
            "why did you call your cat this name?",
        ],
        "currentUtterance": "okay. i love cats. my cat is named putin.",
        "pastResponses": [" no. let's chat about animals. "],
        "pastUtterances": ["let's chat about jesus"],
    }
    gold_results = [{"batch": [{"score": 0.6278616}, {"score": 0.19288766}, {"score": 0.5522217}]}]

    results = requests.post(url, json=request_data).json()[0]["batch"]
    print(results)

    for result, gold_result in zip(results, gold_results[0]["batch"]):
        difference = result["score"] - gold_result["score"]
        assert round(difference, 3) == 0, f"Got\n{result}\n, but expected:\n{gold_result}"

    print("Success")


if __name__ == "__main__":
    main()
