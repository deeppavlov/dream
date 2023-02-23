import requests


def is_container_running(model_url, timeout=4):
    new_url = "/".join(model_url.split("/")[:-1]) + "/ping"
    try:
        response = requests.post(new_url, timeout=timeout)
        if response.status_code == 200:
            return True
    except Exception as exc:
        print(exc)
        return False
    return False
