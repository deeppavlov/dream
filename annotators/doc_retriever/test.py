import requests
import os

SERVICE_PORT = int(os.getenv("SERVICE_PORT"))


def main():
    url_vectorize_documents = f"http://0.0.0.0:{SERVICE_PORT}/vectorize_documents"
    url_return_candidates = f"http://0.0.0.0:{SERVICE_PORT}/return_candidates"
    test_file = "http://files.deeppavlov.ai/dream_data/documents_for_qa/tiny_test_file.txt"
    result_train = requests.post(
        url=url_vectorize_documents,
        json={
            "dialogs": [
                {
                    "human_utterances": ["Hi!"],
                    "human": {
                        "attributes": {
                            "documents_in_use": ["3bFzQ3tc3I_7ed546db9846ba7661ceda123837f7fc"],
                            "processed_documents": {
                                "3bFzQ3tc3I_7ed546db9846ba7661ceda123837f7fc": {
                                    "initial_path_or_link": test_file,
                                    "processed_text_link": test_file,
                                    "filename": "tiny_test_file",
                                }
                            },
                        }
                    },
                }
            ]
        },
    )
    assert result_train.ok, "Failed to reach host. Check if it's up and healthy."
    result_train = result_train.json()[0]
    print(result_train)
    model_info = result_train.get("human_attributes", {}).get("model_info", {})
    assert model_info != {}, f"Got\n{result_train}\n, something is wrong"
    print("vectorize_documents endpoint: success!")
    result_return = requests.post(
        url=url_return_candidates,
        json={
            "dialogs": [
                {
                    "human_utterances": [{"text": "Hi!"}],
                    "human": {
                        "attributes": {
                            "documents_in_use": ["3bFzQ3tc3I_7ed546db9846ba7661ceda123837f7fc"],
                            "processed_documents": {
                                "3bFzQ3tc3I_7ed546db9846ba7661ceda123837f7fc": {
                                    "initial_path_or_link": test_file,
                                    "processed_text_link": test_file,
                                    "filename": "tiny_test_file",
                                }
                            },
                            "model_info": model_info,
                        }
                    },
                }
            ]
        },
    )
    result_return = result_return.json()[0]
    assert result_return.get("candidate_files", []) == [
        "1.txt",
        "2.txt",
    ], f"Got\n{result_return}\n, something is wrong"
    print("return_candidates endpoint: success!")


if __name__ == "__main__":
    main()
