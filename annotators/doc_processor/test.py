import requests
import os

SERVICE_PORT = int(os.getenv("SERVICE_PORT"))


def main():
    url_process_and_upload_doc = f"http://0.0.0.0:{SERVICE_PORT}/process_and_upload_doc"
    test_file = "https://drive.google.com/uc?id=1bL322Ww8nNzGaG0DG41xrq9tS915kzdF"
    result_train = requests.post(
        url=url_process_and_upload_doc,
        json={
            "dialogs": [{"human_utterances": [{"attributes": {"documents": [test_file]}}]}],
            "all_prev_active_skills": [],
        },
    )
    assert result_train.ok, "Failed to reach host. Check if it's up and healthy."
    result_train = result_train.json()[0]
    documents_in_use = result_train.get("human_attributes", {}).get("documents_in_use", [])
    processed_documents = result_train.get("human_attributes", {}).get("processed_documents", {})
    initial_links = [processed_documents[doc_id]["initial_path_or_link"] for doc_id in documents_in_use]
    assert test_file in initial_links, f"Got\n{result_train}\n, something is wrong"
    print("process_and_upload_doc endpoint: success!")


if __name__ == "__main__":
    main()
