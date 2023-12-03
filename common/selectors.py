import yaml
from os import listdir
from typing import List


def collect_descriptions_from_components_folder() -> dict:
    # collect display names and descriptions of skills which descriptions are not given in request
    # from the components folder
    mapping = {}
    for fname in listdir("components/"):
        if "yml" in fname:
            component = yaml.load(open(f"components/{fname}", "r"), Loader=yaml.FullLoader)
            if component["state_manager_method"] == "add_hypothesis" and component["name"] not in mapping.keys():
                mapping[component["name"]] = {
                    "display_name": component["display_name"],
                    "description": component["description"],
                }
    return mapping


def update_descriptions_from_given_dict(
    mapping: dict,
    skills: List[dict],
):
    all_skills = [skill["name"] for skill in skills]
    updated_mapping = {skill_name: v for skill_name, v in mapping.items() if skill_name in all_skills}

    # collect display names and descriptions from the request
    for skill in skills:
        if skill.get("display_name", "") and skill.get("description", ""):
            updated_mapping[skill["name"]] = {
                "display_name": skill["display_name"],
                "description": skill["description"],
            }
    # for the rest of unfound skills, compose description by hands
    for skill in skills:
        if skill["name"] not in updated_mapping.keys():
            prompt = skill["prompt"]
            updated_mapping[skill["name"]] = {
                "display_name": skill["name"],
                "description": f"Agent with the following task:\n`{prompt}`",
            }
    return updated_mapping
