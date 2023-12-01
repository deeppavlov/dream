import json
import os

from pathlib import Path
from typing import List, Union


DEFAULT_SKILLS = ["dummy_skill"]


def get_commands_for_skill(skill_name: str) -> List[str]:
    result = []
    if os.path.isfile(f"./common/commands/{skill_name}_commands.json"):
        list_commands_dicts = json.load(open(f"./common/commands/{skill_name}_commands.json", "r"))
        result = [command_dict["command"] for command_dict in list_commands_dicts]
    return result


def get_command_titles_mapped_to_commands_for_skill(skill_name: str) -> dict:
    result = {}
    if os.path.isfile(f"./common/commands/{skill_name}_commands.json"):
        list_commands_dicts = json.load(open(f"./common/commands/{skill_name}_commands.json", "r"))
        for command_dict in list_commands_dicts:
            result[command_dict["title"]] = command_dict["command"]
    return result


def get_available_commands_mapped_to_skills(available_skill_names: Union[List[str], str]) -> dict:
    if available_skill_names == "all":
        available_skill_names = []
        for json_file_path in os.listdir("./common/commands/"):
            available_skill_names += [Path(json_file_path).name.replace("_commands.json", "")]

    commands_to_skills = {}
    for skill_name in available_skill_names:
        commands_for_skill = get_commands_for_skill(skill_name)
        for command in commands_for_skill:
            if command not in commands_to_skills:
                commands_to_skills[command] = [skill_name]
            else:
                commands_to_skills[command].append(skill_name)

    return commands_to_skills


def get_available_titles_mapped_to_commands(available_skill_names: Union[List[str], str]) -> dict:
    if available_skill_names == "all":
        available_skill_names = []
        for json_file_path in os.listdir("./common/commands/"):
            available_skill_names += [Path(json_file_path).name.replace("_commands.json", "")]

    titles_to_commands = {}
    for skill_name in available_skill_names:
        command_titles_for_skill = get_command_titles_mapped_to_commands_for_skill(skill_name)
        for title, command in command_titles_for_skill.items():
            if title not in titles_to_commands:
                titles_to_commands[title] = [command]
            else:
                titles_to_commands[title].append(command)

    return titles_to_commands


def get_all_skill_names(dialog: dict) -> List[str]:
    pipeline = dialog.get("attributes", {}).get("pipeline", [])
    # pipeline is smth like this: ['annotators.sentseg', 'skills.dummy_skill',
    # 'candidate_annotators.sentence_ranker', 'response_selectors.response_selector', ...]
    all_skill_names = [el.split(".")[1] for el in pipeline if "skills" in el]
    return all_skill_names
