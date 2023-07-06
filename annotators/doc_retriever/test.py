import requests
import os

SERVICE_PORT = int(os.getenv("SERVICE_PORT"))
PARAGRAPHS_NUM = int(os.environ.get("PARAGRAPHS_NUM", 5))


def main():
    url_train_and_upload_model = f"http://0.0.0.0:{SERVICE_PORT}/train_and_upload_model"
    url_return_candidates = f"http://0.0.0.0:{SERVICE_PORT}/return_candidates"
    test_file = "http://files.deeppavlov.ai/dream_data/documents_for_qa/the_little_prince_book.txt"
    result_train = requests.post(
        url=url_train_and_upload_model,
        json={"dialogs": [{"human_attributes": [{"documents": [test_file]}]}]},
    )
    assert result_train.ok, "Failed to reach host. Check if it's up and healthy."
    result_train = result_train.json()[0]
    assert test_file in result_train.get("bot_attributes", {}).get(
        "document_links", []
    ), f"Got\n{result_train}\n, something is wrong"
    print("train_and_upload_model endpoint: success!")
    result_return = requests.post(
        url=url_return_candidates,
        json={
            "dialogs": [
                {
                    "bot": {
                        "attributes": {
                            "db_link": result_train.get("bot_attributes", {}).get("db_link", ""),
                            "matrix_link": result_train.get("bot_attributes", {}).get("matrix_link", ""),
                        }
                    },
                    "human_utterances": [{"text": "Who is the Little Prince?"}],
                }
            ]
        },
    ).json()[0]
    assert (
        len(result_return.get("candidate_files", [])) == PARAGRAPHS_NUM
    ), f"Got\n{result_return}\n, something is wrong"
    print("return_candidates endpoint: success!")


if __name__ == "__main__":
    main()
