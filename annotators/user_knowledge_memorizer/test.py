from pathlib import Path
import os
import requests
from deeppavlov_kg import TerminusdbKnowledgeGraph


def formulate_utt_annotations(dog_id=None, park_id=None):
    utt_annotations = {
        "property_extraction": [{
            "triplets": [
                {"subject": "user", "relation": "HAVE PET", "object": "dog"},
                {"subject": "user", "relation": "LIKE GOTO", "object": "park"},
            ]
        }],
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
                "entity_id_tags": ["Animal"],
            },
        )
    if park_id is not None:
        utt_annotations["custom_entity_linking"].append(
            {
                "entity_substr": "park",
                "entity_ids": [park_id],
                "confidences": [1.0],
                "tokens_match_conf": [1.0],
                "entity_id_tags": ["Place"],
            },
        )

    return utt_annotations


def prepare_for_comparison(results):
    for result in results:
        if triplets := result["added_to_graph"]:
            for triplet in triplets:
                triplet[2] = triplet[2].split("/")[0]
        if triplets := result["triplets_already_in_graph"]:
            for triplet in triplets:
                triplet[2] = triplet[2].split("/")[0]

    return results


def compare_results(results, golden_results) -> bool:
    def compare(triplets, golden_result):
        for triplet in triplets:
            if triplet not in golden_result:
                return False
        return True

    is_successfull = []
    for result, golden_result in zip(results, golden_results):
        is_added = compare(result["added_to_graph"], golden_result["added_to_graph"])
        is_in_graph = compare(result["triplets_already_in_graph"], golden_result["triplets_already_in_graph"])
        is_successfull.append(is_added)
        is_successfull.append(is_in_graph)
    return all(is_successfull)


def main():
    TERMINUSDB_SERVER_URL = "http://0.0.0.0:6363"
    TERMINUSDB_SERVER_TEAM = "admin"
    TERMINUSDB_SERVER_DB = "user_knowledge_db"
    TERMINUSDB_SERVER_PASSWORD = "root"
    INDEX_LOAD_PATH = Path(os.path.expanduser("annotators/user_knowledge_memorizer"))
    USER_KG_PORT = 8027

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
        entities_info = graph.get_properties_of_entities(
            [*user_props["HAVE PET/Animal"], *user_props["LIKE GOTO/Place"]]
        )
        for entity_info in entities_info:
            if entity_info.get("substr") == "dog":
                dog_id = entity_info["@id"]
            elif entity_info.get("substr") == "park":
                park_id = entity_info["@id"]
        print(f"Found park_id: '{park_id}' and dog_ig: '{dog_id}'")
        added_new_entities = False
    except Exception:
        print("Adding new entities and rels")
        added_new_entities = True

    request_data = [
        {
            "utterances": [
                {
                    "text": "i have a dog and a cat",
                    "user": {"id": USER_ID.split("/")[1]},
                    "annotations": formulate_utt_annotations(dog_id, park_id),
                }
            ]
        }
    ]

    golden_triplets = [[USER_ID, "LIKE GOTO", "Place"], [USER_ID, "HAVE PET", "Animal"]]
    if added_new_entities:
        golden_results = [[{"added_to_graph": golden_triplets, "triplets_already_in_graph": []}]]
    else:
        golden_results = [[{"added_to_graph": [], "triplets_already_in_graph": golden_triplets}]]

    count = 0
    for data, golden_result in zip(request_data, golden_results):
        result = requests.post(USER_KG_URL, json=data).json()
        print(result)
        result = prepare_for_comparison(result)
        if compare_results(result, golden_result):
            count += 1
    assert count == len(request_data)
    print("Success")


if __name__ == "__main__":
    main()
