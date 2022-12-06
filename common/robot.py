import json
import requests


ROS_FSM_SERVER = "http://172.17.0.1:5000"
ROS_FSM_INTENT_ENDPOINT = f"{ROS_FSM_SERVER}/upload_response"
ROS_FSM_IS_COMMAND_VALID_ENDPOINT = f"{ROS_FSM_SERVER}/is_command_valid"
ROS_FSM_IS_COMMAND_PERFORMED_ENDPOINT = f"{ROS_FSM_SERVER}/is_command_performed"


def check_if_valid_robot_command(command):
    result = requests.post(ROS_FSM_IS_COMMAND_VALID_ENDPOINT, data=json.dumps({"command": command}))
    if result.status_code == 200:
        if result.json().get("valid", False):
            return True
    return False


def send_robot_command_to_perform(command):
    result = requests.post(ROS_FSM_INTENT_ENDPOINT, data=json.dumps({"text": command}))
    if result.status_code == 200:
        if result.json().get("accepted", False):
            return True
    return False


def check_if_command_performed(command):
    result = requests.post(ROS_FSM_IS_COMMAND_PERFORMED_ENDPOINT, data=json.dumps({"command": command}))
    if result.status_code == 200:
        if result.json().get("performed", False):
            return True
    return False
