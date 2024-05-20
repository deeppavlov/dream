import requests
import logging


# def check_if_valid_robot_command(command, service_url, dialog_id, timeout=1.0):
#     result = requests.post(
#         f"{service_url}/is_command_valid", json={"command": command, "dialog_id": dialog_id}, timeout=timeout
#     )
#     if result.status_code == 200:
#         if result.json().get("result", False):
#             return True
#     return False

DEF_FWD = 1.0
DEF_SID = 0.0
DEF_ROT = 0.0

def formulate_json(FWD=DEF_FWD, SID=DEF_SID, ROT=DEF_ROT, TXT=""):
    if TXT:
        return {
                "command": {
                    "name": "talk",
                    "args": {
                        "text": TXT
                    }
                }
            }
    return {
            "command": {
                "name": "cmd_vel",
                "args": {
                    "forward": FWD,
                    "side": SID,
                    "rotate": ROT
                }
            }
        }


def send_robot_command_to_perform(command, service_url, dialog_id, timeout=1.0):

    # INFO: a service should do this logic

    _txt = "hello" if command == "move_forward" else ""
    _request_data = formulate_json(TXT=_txt)

    # INFO: EOS

    logging.info(f"formulating json: {_request_data}")

    result = requests.post(
        f"{service_url}/perform_command", json=_request_data, timeout=timeout
    )
    logging.info(f"request sent to {service_url}")
    if result.status_code == 200:
        if result.json().get("result", False):
            logging.info(f"Response from robot received successfully for intent: {command}")
            return True
    logging.info(f"Failed to receive response from robot for intent: {command}")
    return False


# def check_if_command_performed(command, service_url, dialog_id, timeout=1.0):
#     result = requests.post(
#         f"{service_url}/is_command_performed", json={"command": command, "dialog_id": dialog_id}, timeout=timeout
#     )
#     if result.status_code == 200:
#         if result.json().get("result", False):
#             return True
#     return False
