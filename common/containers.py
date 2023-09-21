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


def get_envvars_for_llm(model_url, timeout=4):
    new_url = "/".join(model_url.split("/")[:-1]) + "/envvars_to_send"
    try:
        response = requests.post(new_url, timeout=timeout)
        if response.status_code == 200:
            return response.json()
    except Exception as exc:
        print(exc)
        return []
    return []


def get_max_tokens_for_llm(model_url, timeout=4):
    new_url = "/".join(model_url.split("/")[:-1]) + "/max_tokens"
    try:
        response = requests.post(new_url, timeout=timeout)
        if response.status_code == 200:
            return response.json()
    except Exception as exc:
        print(exc)
        return 1000
    return 1000
