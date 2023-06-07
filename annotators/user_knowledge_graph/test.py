from pathlib import Path
import os
import requests
from deeppavlov_kg import TerminusdbKnowledgeGraph
from dotenv import load_dotenv

load_dotenv("./.env")
load_dotenv("./.env_secret")


def formulate_utt_annotations(dog_id=None, park_id=None):
    utt_annotations = {
        "property_extraction": {
            "triplets": [
                {"subject": "user", "relation": "have_pet", "object": "dog"},
                {"subject": "user", "relation": "like_goto", "object": "park"},
            ]
        },
        "custom_entity_linking": [],
    }

    # if dog is in kg add it to custom_el annotations
    if dog_id is not None:
        utt_annotations["custom_entity_linking"].append(
            {
                "entity_substr": "dog",
                "entity_ids": [dog_id],
                "confidences": [1.0],
                "tokens_match_conf": [1.0],
                "entity_id_tags": ["animal"],
            },
        )
    if park_id is not None:
        utt_annotations["custom_entity_linking"].append(
            {
                "entity_substr": "park",
                "entity_ids": [park_id],
                "confidences": [1.0],
                "tokens_match_conf": [1.0],
                "entity_id_tags": ["Misc"],
            },
        )

    return utt_annotations


def format_for_comparison(results):
    for result in results:
        if result["added_to_graph"]:
            for entity in result["added_to_graph"]:
                del entity["entity_ids"]
        elif result["triplets_already_in_graph"]:
            for triplet in result["triplets_already_in_graph"]:
                triplet[2] = triplet[2].split("/")[0]
        else:
            print("Error: no result returned")
    return results


def compare_results(results, golden_results):
    for result, golden_result in zip(results, golden_results):
        if result["added_to_graph"]:
            return result == golden_result
        elif triplets:= result["triplets_already_in_graph"]:
            for triplet in triplets:
                if triplet in golden_result["triplets_already_in_graph"]:
                    return True
    return False


def main():    
    TERMINUSDB_SERVER_URL = os.getenv("TERMINUSDB_SERVER_URL")
    TERMINUSDB_SERVER_PASSWORD = os.getenv("TERMINUSDB_SERVER_PASSWORD")
    assert TERMINUSDB_SERVER_PASSWORD, "TerminusDB server password is not specified in env"
    TERMINUSDB_SERVER_DB = os.getenv("TERMINUSDB_SERVER_DB")
    TERMINUSDB_SERVER_TEAM = os.getenv("TERMINUSDB_SERVER_TEAM")
    INDEX_LOAD_PATH = Path(os.path.expanduser("annotators/user_knowledge_graph"))
    USER_KG_PORT = 9138

    USER_KG_URL = f"http://0.0.0.0:{USER_KG_PORT}/respond"

    graph = TerminusdbKnowledgeGraph(
        db_name=TERMINUSDB_SERVER_DB,
        team=TERMINUSDB_SERVER_TEAM,
        server=TERMINUSDB_SERVER_URL,
        password=TERMINUSDB_SERVER_PASSWORD,
        index_load_path=INDEX_LOAD_PATH,
    )

    USER_ID = "User/b75d2700259bdc44sdsdf85e7f530ed"
    # get dog_id and park_id from KG
    dog_id, park_id = None, None
    try:
        user_props = graph.get_properties_of_entity(USER_ID)
        entities_info = graph.get_properties_of_entities([*user_props["HAVE_PET/animal"], *user_props["LIKE_GOTO/Misc"]])
        for entity_info in entities_info:
            if entity_info.get("Name") == "dog":
                dog_id = entity_info["@id"]
            elif entity_info.get("Name") == "park":
                park_id = entity_info["@id"]
        print(f"Found park_id: '{park_id}' and dog_ig: '{dog_id}'")
        added_new_entities = False
    except Exception:
        print("User isn't found")
        added_new_entities = True

    request_data = [
        {
            "utterances": [{
                "text": "i have a dog and a cat",
                "user": {"id": USER_ID.split("/")[1]},
                "annotations": formulate_utt_annotations(dog_id, park_id),
            }]
        }
    ]

    if added_new_entities:
        golden_results = [
            [{
                "added_to_graph": [{
                    "entity_kinds": ["animal", "Misc"],
                    "entity_names": ["dog", "park"],
                    "rel_names": ["HAVE_PET", "LIKE_GOTO"]
                }],
                "triplets_already_in_graph": []
            }]
        ]
    else:
        golden_results = [
            [{
                "added_to_graph": [],
                "triplets_already_in_graph": [
                    [USER_ID, "LIKE_GOTO", "Misc"],
                    [USER_ID, "HAVE_PET", "animal"]
                ]
            }]
        ]

    count = 0
    for data, golden_result in zip(request_data, golden_results):
        result = requests.post(USER_KG_URL, json=data).json()
        result = format_for_comparison(result)
        if compare_results(result, golden_result):
            count += 1
    assert count == len(request_data)
    print("Success")


if __name__ == "__main__":
    main()
