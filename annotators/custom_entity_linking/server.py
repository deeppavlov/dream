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


def preprocess_context(context_batch):
    """Preprocesses the context batch by combining previous and current utterances.

    Args:
      context_batch (list): List of conversation contexts.

    Returns:
      list: Preprocessed context batch.
    """
    optimized_context_batch = []
    for hist_uttr in context_batch:
        if len(hist_uttr) == 1:
            optimized_context_batch.append(hist_uttr[0])
        else:
            prev_uttr = hist_uttr[-2]
            cur_uttr = hist_uttr[-1]
            is_q = (
                any([prev_uttr.startswith(q_word) for q_word in ["what ", "who ", "when ", "where "]])
                or "?" in prev_uttr
            )
            if is_q and len(cur_uttr.split()) < 3:
                optimized_context_batch.append(f"{prev_uttr} {cur_uttr}")
            else:
                optimized_context_batch.append(cur_uttr)

    return optimized_context_batch


def process_entity_info(
    entity_substr_batch, entity_ids_batch, conf_batch, entity_id_tags_batch, prex_info_batch, optimized_context_batch
):
    """Processes entity information based on various conditions.

    Args:
      entity_substr_batch (list): List of entity substrings (entity names).
      entity_ids_batch (list): List of entity IDs.
      conf_batch (list): List of confidences.
      entity_id_tags_batch (list): List of entity ID tags (entity kinds).
      prex_info_batch (list): List of property extraction information.
      optimized_context_batch (list): List of preprocessed conversation contexts.

    Returns:
      list: Processed entity information batch.
    """
    entity_info_batch = []
    for (
        entity_substr_list,
        entity_ids_list,
        conf_list,
        entity_id_tags_list,
        prex_info,
        context,
    ) in zip(
        entity_substr_batch,
        entity_ids_batch,
        conf_batch,
        entity_id_tags_batch,
        prex_info_batch,
        optimized_context_batch,
    ):
        entity_info_list = []
        triplets = {}

        # Extract triplets from property extraction information
        if isinstance(prex_info, list) and prex_info:
            prex_info = prex_info[0]
        if prex_info:
            triplets = prex_info.get("triplets", {})

        obj2rel_dict = {}
        for triplet in triplets:
            obj = triplet["object"].lower()

            # Determine the relationship type (relation or property)
            if "relation" in triplet:
                rel = triplet["relation"]
            elif "property" in triplet:
                rel = triplet["property"]
            else:
                rel = ""
            obj2rel_dict[obj] = rel

        # Process entity information for each entity substring
        for entity_substr, entity_ids, confs, entity_id_tags in zip(
            entity_substr_list,
            entity_ids_list,
            conf_list,
            entity_id_tags_list,
        ):
            entity_info = {}
            entity_substr = entity_substr.lower()
            context = context.lower()
            curr_rel = obj2rel_dict.get(entity_substr, "")
            is_abstract = curr_rel.lower().replace("_", " ") in abstract_rels and not any(
                [f" {word} {entity_substr}" in context for word in ["the", "my", "his", "her"]]
            )

            filtered_entity_ids, filtered_confs, filtered_entity_id_tags = [], [], []

            # Filter entity information based on condition:
            # - Exclude entities marked as "Abstract" in db if they are not considered
            # abstract according to is_abstract.
            for entity_id, conf, entity_id_tag in zip(entity_ids, confs, entity_id_tags):
                if entity_id_tag.startswith("Abstract") and not is_abstract:
                    pass
                else:
                    filtered_entity_ids.append(entity_id)
                    filtered_confs.append(conf)
                    filtered_entity_id_tags.append(entity_id_tag)

            if filtered_entity_ids and entity_substr in context:
                # Construct the entity information dictionary
                entity_info["entity_substr"] = entity_substr
                entity_info["entity_ids"] = filtered_entity_ids
                entity_info["confidences"] = [float(elem[2]) for elem in filtered_confs]
                entity_info["tokens_match_conf"] = [float(elem[0]) for elem in filtered_confs]
                entity_info["entity_id_tags"] = filtered_entity_id_tags
                entity_info_list.append(entity_info)
        # Add the processed entity information to the batch
        entity_info_batch.append(entity_info_list)
    return entity_info_batch


@app.route("/model", methods=["POST"])
def respond():
    """Main function for responding to a request.

    Returns:
      flask.Response: Response containing the processed entity information.
    """
    st_time = time.time()
    user_ids = request.json.get("user_id", [""])
    entity_substr_batch = request.json.get("entity_substr", [[""]])
    entity_tags_batch = request.json.get(
        "entity_tags",
        [["" for _ in entity_substr_list] for entity_substr_list in entity_substr_batch],
    )
    context_batch = request.json.get("context", [[""]])
    prex_info_batch = request.json.get("property_extraction", [{} for _ in entity_substr_batch])

    # Preprocess the conversation context
    optimized_context_batch = preprocess_context(context_batch)

    entity_info_batch = []
    try:
        (
            entity_substr_batch,
            entity_ids_batch,
            conf_batch,
            entity_id_tags_batch,
        ) = el(user_ids, entity_substr_batch, entity_tags_batch)

        # Process entity information
        entity_info_batch = process_entity_info(
            entity_substr_batch,
            entity_ids_batch,
            conf_batch,
            entity_id_tags_batch,
            prex_info_batch,
            optimized_context_batch,
        )

    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
        entity_info_batch = [[]] * len(entity_substr_batch)

    total_time = time.time() - st_time
    logger.info(f"entity_info_batch: {entity_info_batch}")
    logger.info(f"custom entity linking exec time = {total_time:.3f}s")

    # Return the processed entity information
    return jsonify(entity_info_batch)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
