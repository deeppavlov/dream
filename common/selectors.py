import yaml

from os import listdir
from typing import List


def collect_descriptions_from_components(skills: List[dict]):
    # skills contain list of working names (aka `dff_blabla_skill`)
    result = []
    all_skills = [skill["name"] for skill in skills]
    collected_skills = []
    display_names_mapping = {}

    # collect display names and descriptions from the request
    for skill in skills:
        if skill.get("display_name", "") and skill.get("description", ""):
            result += [(skill["display_name"], skill["description"])]
            collected_skills += [skill["name"]]
            display_names_mapping[skill["name"]] = skill["display_name"]

    # collect display names and descriptions of skills which descriptions are not given in request
    # from the components folder
    for fname in listdir("components/"):
        if "yml" in fname:
            component = yaml.load(open(f"components/{fname}", "r"), Loader=yaml.FullLoader)
            if component["name"] in all_skills and component["name"] not in collected_skills:
                result += [(component["display_name"], component["description"])]
                collected_skills += [component["name"]]
                display_names_mapping[component["name"]] = component["display_name"]

    # for the rest of unfound skills, compose description by hands
    for skill in skills:
        if skill["name"] not in collected_skills:
            prompt = skill["prompt"]
            result += [(skill["name"], f"Agent with the following task:\n`{prompt}`")]
            display_names_mapping[skill["name"]] = skill["name"]

    return result, display_names_mapping
