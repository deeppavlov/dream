import requests
from deeppavlov_kg import TerminusdbKnowledgeGraph


def formulate_utt_annotations(dog_id=None, park_id=None):
    utt_annotations = {
        "property_extraction": [
            {
                "triplets": [
                    {"subject": "user", "relation": "HAVE PET", "object": "dog"},
                    {"subject": "user", "relation": "LIKE GOTO", "object": "park"},
                ]
            }
        ],
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
        if uttrs := result["added_to_graph"]:
            for utt in uttrs:
                for triplet in utt:
                    triplet[2] = triplet[2].split("/")[0]
        if uttrs := result["triplets_already_in_graph"]:
            for utt in uttrs:
                for triplet in utt:
                    triplet[2] = triplet[2].split("/")[0]

    return results


def compare_results(results, golden_results) -> bool:
    def compare(uttrs, golden_result):
        for idx, utt in enumerate(uttrs):
            for triplet in utt:
                if triplet not in golden_result[idx]:
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
    TERMINUSDB_SERVER_DB = "bot_knowledge_db"
    TERMINUSDB_SERVER_PASSWORD = "root"
    BOT_KNOWLEDGE_MEMORIZER_PORT = 8044

    BOT_KNOWLEDGE_MEMORIZER_URL = f"http://0.0.0.0:{BOT_KNOWLEDGE_MEMORIZER_PORT}/respond"

    graph = TerminusdbKnowledgeGraph(
        db_name=TERMINUSDB_SERVER_DB,
        team=TERMINUSDB_SERVER_TEAM,
        server=TERMINUSDB_SERVER_URL,
        password=TERMINUSDB_SERVER_PASSWORD,
    )

    BOT_ID = "Bot/514b2c3d-bb73-4294-9486-04f9e099835e"
    # get dog_id and park_id from KG
    dog_id, park_id = None, None
    try:
        user_props = graph.get_properties_of_entity(BOT_ID)
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
                    "user": {"id": BOT_ID.split("/")[1]},
                    "annotations": formulate_utt_annotations(dog_id, park_id),
                },
                {
                    "text": "",
                    "user": {"id": ""},
                    "annotations": {
                        "property_extraction": [{}],
                        "custom_entity_linking": [],
                    },
                },
            ],
            "human_utterances": [
                {
                    "text": "What's your dog's name?",
                },
                {
                    "text": "",
                },
            ],
        }
    ]

    golden_triplets = [[[BOT_ID, "LIKE GOTO", "Place"], [BOT_ID, "HAVE PET", "Animal"]], []]
    if added_new_entities:
        golden_results = [[{"added_to_graph": golden_triplets, "triplets_already_in_graph": [[], []]}]]
    else:
        golden_results = [[{"added_to_graph": [[], []], "triplets_already_in_graph": golden_triplets}]]

    count = 0
    for data, golden_result in zip(request_data, golden_results):
        result = requests.post(BOT_KNOWLEDGE_MEMORIZER_URL, json=data).json()
        print(result)
        result = prepare_for_comparison(result)
        if compare_results(result, golden_result):
            count += 1
    assert count == len(request_data)
    print("Success")


if __name__ == "__main__":
    main()
