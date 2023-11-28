import json
import os

from pathlib import Path
from typing import List, Union


DEFAULT_SKILLS = ["dummy_skill"]


def write_commands_from_file_to_dict(skill_name, commands_to_skills, json_file_path):
    list_commands = json.load(open(json_file_path, "r"))
    for command in list_commands:
        if command not in commands_to_skills:
            commands_to_skills[command] = [skill_name]
        else:
            commands_to_skills[command].append(skill_name)
    return commands_to_skills


def get_available_commands(available_skill_names: Union[List[str], str]) -> List[str]:
    commands_to_skills = {}
    if available_skill_names == "all":
        for json_file_path in os.listdir("./common/commands/"):
            skill_name = Path(json_file_path).name.replace("_commands.json", "")
            commands_to_skills = write_commands_from_file_to_dict(skill_name, commands_to_skills, json_file_path)
    else:
        for skill_name in available_skill_names:
            json_file_path = f"common/commands/{skill_name}_commands.json"
            if os.path.isfile(json_file_path):
                commands_to_skills = write_commands_from_file_to_dict(skill_name, commands_to_skills, json_file_path)
    return commands_to_skills
