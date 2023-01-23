import requests


def is_container_running(model_url, timeout=4):
    try:
        requested_data = [{"speaker": "human", "text": "hi"}]
        response = requests.post(model_url, json={"dialog_contexts": [requested_data]}, timeout=timeout)
        if response.status_code == 200:
            return True
    except Exception as exc:
        print(exc)
        return False
    return False
