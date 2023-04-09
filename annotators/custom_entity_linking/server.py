import logging
import os
import time
from flask import Flask, request, jsonify
import sentry_sdk
from deeppavlov import build_model

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
sentry_sdk.init(os.getenv("SENTRY_DSN"))

app = Flask(__name__)

config_name = os.getenv("CONFIG")

with open("abstract_rels.txt", "r") as inp:
    abstract_rels = [line.strip() for line in inp.readlines()]

try:
    el = build_model(config_name, download=True)
    logger.info("model loaded")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e


@app.route("/add_entities", methods=["POST"])
def add_entities():
    user_id = request.json.get("user_id", "")
    entity_info = request.json.get("entity_info", {})
    entity_substr_list = entity_info.get("entity_substr", [])
    entity_ids_list = entity_info.get("entity_ids", [])
    tags_list = entity_info.get("tags", [])
    el[0].add_custom_entities(user_id, entity_substr_list, entity_ids_list, tags_list)
    logger.info(f"added entities {entity_info}")
    return {}


def preprocess_hist_utt(context_batch):
    opt_context_batch = []
    for hist_utt in context_batch:
        hist_utt = [utt for utt in hist_utt if len(utt) > 1]
        last_utt = hist_utt[-1]
        if last_utt[-1] not in {".", "!", "?"}:
            last_utt = f"{last_utt}."
        if len(hist_utt) > 1:
            prev_utt = hist_utt[-2]
            if prev_utt[-1] not in {".", "!", "?"}:
                prev_utt = f"{prev_utt}."
            opt_context_batch.append([prev_utt, last_utt])
        else:
            opt_context_batch.append([last_utt])
    return opt_context_batch


def define_entity_info(prex_info, context, substr_list, ids_list, conf_list, id_tags_list):
    entity_info_list = []
    triplet = dict()
    if isinstance(prex_info, list) and prex_info:
        prex_info = prex_info[0]
    if prex_info:
        triplet = prex_info.get("triplet", {})
    rel = ""
    if "relation" in triplet:
        rel = triplet["relation"]
    elif "property" in triplet:
        rel = triplet["property"]
    for substr, ids, confs, id_tags in zip(substr_list, ids_list, conf_list, id_tags_list):
        entity_info = {}
        is_abstract = rel.lower().replace("_", " ") in abstract_rels and not any(
            [f" {word} {substr}" in context for word in ["the", "my", "his", "her"]]
        )

        f_ids, f_confs, f_id_tags = [], [], []
        for entity_id, conf, id_tag in zip(ids, confs, id_tags):
            if id_tag.startswith("Abstract") and not is_abstract:
                pass
            else:
                f_ids.append(entity_id)
                f_confs.append(conf)
                f_id_tags.append(id_tag)

        if f_ids:
            entity_info["entity_substr"] = substr
            entity_info["entity_ids"] = f_ids
            entity_info["confidences"] = [float(elem[2]) for elem in f_confs]
            entity_info["tokens_match_conf"] = [float(elem[0]) for elem in f_confs]
            entity_info["entity_id_tags"] = f_id_tags
            entity_info_list.append(entity_info)
    return entity_info_list


@app.route("/model", methods=["POST"])
def respond():
    st_time = time.time()
    user_ids = request.json.get("user_id", [""])
    substr_batch = request.json.get("entity_substr", [[""]])
    tags_batch = request.json.get("entity_tags", [["" for _ in substr_list] for substr_list in substr_batch])
    context_batch = request.json.get("context", [[""]])
    prex_info_batch = request.json.get("property_extraction", [dict() for _ in substr_batch])
    opt_context_batch = preprocess_hist_utt(context_batch)

    entity_info_batch = [[dict()] for _ in substr_batch]
    try:
        substr_batch, ids_batch, conf_batch, id_tags_batch = el(user_ids, substr_batch, tags_batch, opt_context_batch)
        entity_info_batch = []
        for (substr_list, ids_list, conf_list, id_tags_list, prex_info, context) in zip(
            substr_batch, ids_batch, conf_batch, id_tags_batch, prex_info_batch, opt_context_batch
        ):
            if context:
                context = " ".join(context)
            else:
                context = ""
            entity_info_list = define_entity_info(prex_info, context, substr_list, ids_list, conf_list, id_tags_list)
            entity_info_batch.append(entity_info_list)
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
    total_time = time.time() - st_time
    logger.info(f"entity_info_batch: {entity_info_batch}")
    logger.info(f"custom entity linking exec time = {total_time:.3f}s")
    return jsonify(entity_info_batch)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
