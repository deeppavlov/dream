import requests


command_intents = {"track_object", "turn_around", "move_forward", "move_backward", "open_door", "move_to_point"}
embodied_intents = {"test_command", "move_forward", "move_backward"}


def check_if_valid_robot_command(command, service_url, dialog_id, timeout=1.0):
    result = requests.post(
        f"{service_url}/is_command_valid", json={"command": command, "dialog_id": dialog_id}, timeout=timeout
    )
    if result.status_code == 200:
        if result.json().get("result", False):
            return True
    return False


def send_robot_command_to_perform(command, service_url, dialog_id, timeout=1.0):
    result = requests.post(
        f"{service_url}/perform_command", json={"command": command, "dialog_id": dialog_id}, timeout=timeout
    )
    if result.status_code == 200:
        if result.json().get("result", False):
            return True
    return False


def check_if_command_performed(command, service_url, dialog_id, timeout=1.0):
    result = requests.post(
        f"{service_url}/is_command_performed", json={"command": command, "dialog_id": dialog_id}, timeout=timeout
    )
    if result.status_code == 200:
        if result.json().get("result", False):
            return True
    return False
