import requests


def is_container_running(model_url, json_data, timeout=4):
    try:
        response = requests.post(model_url, json=json_data, timeout=timeout)
        if response.status_code == 200:
            return True
    except Exception as exc:
        print(exc)
        return False
    return False
