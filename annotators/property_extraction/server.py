import logging
import os
import re
import time

import nltk
import sentry_sdk
from flask import Flask, jsonify, request

from deeppavlov import build_model

sentry_sdk.init(os.getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__)

stemmer = nltk.PorterStemmer()

config_name = os.getenv("CONFIG")
rel_cls_flag = int(os.getenv("REL_CLS_FLAG", "0"))

rel_type_dict = {}
with open("rel_list.txt", "r") as fl:
    lines = fl.readlines()
    for line in lines:
        rel, rel_type = line.strip().split()
        if rel_type == "r":
            rel_type = "relation"
        else:
            rel_type = "property"
        rel_type_dict[rel.replace("_", " ")] = rel_type


def check_triplet(triplet):
    if triplet[0] in {"hi", "hello"} or any([word in triplet[0] for word in {" hi ", " hello "}]):
        return False
    return True


try:
    generative_ie = build_model(config_name, download=True)
    logger.info("property extraction model is loaded.")
    if rel_cls_flag:
        rel_cls = build_model("property_classification_distilbert.json")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e


def get_result(request):
    st_time = time.time()
    uttrs = request.json.get("utterances", [])
    entities_with_labels_batch = request.json.get("entities_with_labels", [[] for _ in uttrs])
    entity_info_batch = request.json.get("entity_info", [[] for _ in uttrs])

    triplets_batch = []
    outputs, scores = generative_ie(uttrs)
    for output in outputs:
        triplet = ""
        fnd = re.findall(r"<subj> (.*?)<rel> (.*?)<obj> (.*)", output)
        if fnd:
            triplet = list(fnd[0])
            if triplet[0] == "i":
                triplet[0] = "user"
        triplets_batch.append(triplet)
    logger.info(f"outputs {outputs} scores {scores} triplets_batch {triplets_batch}")
    if rel_cls_flag:
        rels = rel_cls(uttrs)
        logger.info(f"classified relations: {rels}")
        filtered_triplets_batch = []
        for triplet, rel in zip(triplets_batch, rels):
            rel = rel.replace("_", " ")
            if len(triplet) == 3 and triplet[1] == rel and check_triplet(triplet):
                filtered_triplets_batch.append(triplet)
            else:
                filtered_triplets_batch.append([])
        triplets_batch = filtered_triplets_batch

    triplets_info_batch = []
    for triplet, uttr, entities_with_labels, entity_info_list in zip(
        triplets_batch, uttrs, entities_with_labels_batch, entity_info_batch
    ):
        uttr = uttr.lower()
        entity_substr_dict = {}
        formatted_triplet = {}
        if len(uttr.split()) > 2:
            for entity in entities_with_labels:
                if "text" in entity:
                    entity_substr = entity["text"]
                    if "offsets" in entity:
                        start_offset, end_offset = entity["offsets"]
                    else:
                        start_offset = uttr.find(entity_substr.lower())
                        end_offset = start_offset + len(entity_substr)
                    offsets = [start_offset, end_offset]
                    if triplet and entity_substr in [triplet[0], triplet[2]]:
                        entity_substr_dict[entity_substr] = {"offsets": offsets}
            if entity_info_list:
                for entity_info in entity_info_list:
                    if entity_info and "entity_substr" in entity_info and "entity_ids" in entity_info:
                        entity_substr = entity_info["entity_substr"]
                        if triplet and (
                            entity_substr in [triplet[0], triplet[2]]
                            or stemmer.stem(entity_substr) in [triplet[0], triplet[2]]
                        ):
                            if entity_substr not in entity_substr_dict:
                                entity_substr_dict[entity_substr] = {}
                            entity_substr_dict[entity_substr]["entity_ids"] = entity_info["entity_ids"]
                            entity_substr_dict[entity_substr]["dbpedia_types"] = entity_info.get("dbpedia_types", [])
                            entity_substr_dict[entity_substr]["finegrained_types"] = entity_info.get(
                                "entity_id_tags", []
                            )
        if triplet:
            formatted_triplet = {"subject": triplet[0], rel_type_dict[triplet[1]]: triplet[1], "object": triplet[2]}
        triplets_info_batch.append({"triplet": formatted_triplet, "entity_info": entity_substr_dict})

    total_time = time.time() - st_time
    logger.info(f"property extraction exec time: {total_time: .3f}s")
    logger.info(f"property extraction, input {uttrs}, output {triplets_info_batch} scores {scores}")
    return triplets_info_batch


@app.route("/respond", methods=["POST"])
def respond():
    result = get_result(request)
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8130)
