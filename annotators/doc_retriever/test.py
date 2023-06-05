import requests
import os

SERVICE_PORT = int(os.getenv("SERVICE_PORT"))


def main_test():
    url = "http://0.0.0.0:{SERVICE_PORT}/return_candidates"
    result = requests.post(
        url=url,
        json={
            "sentences": [
                ["What are some of the risks that Apple faces?"],
                [
                    "Hello, what can you do?",
                    "Hello, I can answer questions based on the document you provide."
                    "Ok, give me overview of Apple net sales by region",
                ],
            ]
        },
    )
    assert result.ok, "Failed to reach host. Check if it's up and healthy."
    assert len(result) and [all(len(sample[0]) > 0 for sample in result)], f"Got\n{result}\n, something is wrong"
    print("Success!")


if __name__ == "__main__":
    main_test()
