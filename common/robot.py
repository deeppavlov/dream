import json
import requests


def check_if_valid_robot_command(command, service_url, dialog_id):
    result = requests.post(
        f"{service_url}/is_command_valid",
        data=json.dumps({"command": command, "dialog_id": dialog_id}),
        timeout=1.0
    )
    if result.status_code == 200:
        if result.json().get("valid", False):
            return True
    return False


def send_robot_command_to_perform(command, service_url, dialog_id):
    result = requests.post(
        f"{service_url}/upload_response",
        data=json.dumps({"text": command, "dialog_id": dialog_id}),
        timeout=1.0
    )
    if result.status_code == 200:
        if result.json().get("accepted", False):
            return True
    return False


def check_if_command_performed(command, service_url, dialog_id):
    result = requests.post(
        f"{service_url}/is_command_performed",
        data=json.dumps({"command": command, "dialog_id": dialog_id}),
        timeout=1.0
    )
    if result.status_code == 200:
        if result.json().get("performed", False):
            return True
    return False
