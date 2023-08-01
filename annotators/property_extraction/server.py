import logging
import os
import re
import time
import pickle
import itertools
import json

import nltk
import sentry_sdk
import spacy
import numpy as np
from flask import Flask, jsonify, request

from deeppavlov import build_model
from src.sentence_answer import sentence_answer

sentry_sdk.init(os.getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)
app = Flask(__name__)

stemmer = nltk.PorterStemmer()
nlp = spacy.load("en_core_web_sm")

t5_config = os.getenv("CONFIG_T5")
rel_ranker_config = os.getenv("CONFIG_REL_RANKER")
add_entity_info = int(os.getenv("ADD_ENTITY_INFO", "0"))

try:
    generative_ie = build_model(t5_config, download=True)
    rel_ranker = build_model(rel_ranker_config, download=True)
    logger.info("property extraction model is loaded.")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

rel_type_dict = {}
relations_all = []
with open("rel_list.txt", "r") as fl:
    lines = fl.readlines()
    for line in lines:
        rel, rel_type = line.strip().split()
        relations_all.append(rel.replace("_", " "))
        if rel_type == "r":
            rel_type = "relation"
        else:
            rel_type = "property"
        rel_type_dict[rel.replace("_", " ")] = rel_type

config_metadata = json.load(open(rel_ranker_config))["metadata"]["variables"]
root_path = config_metadata["ROOT_PATH"]
model_path = config_metadata["MODEL_PATH"].replace("{ROOT_PATH}", root_path)
rels_path = os.path.expanduser(f"{model_path}/rel_groups.pickle")
with open(rels_path, "rb") as fl:
    rel_groups_list = pickle.load(fl)


def sentrewrite(sentence, init_answer):
    answer = init_answer.strip(".")
    if any([sentence.startswith(elem) for elem in ["what's", "what is"]]):
        for old_tok, new_tok in [
            ("what's your", f"{answer} is my"),
            ("what is your", f"{answer} is my"),
            ("what is", f"{answer} is"),
            ("what's", f"{answer} is"),
        ]:
            sentence = sentence.replace(old_tok, new_tok)
    elif any([sentence.startswith(elem) for elem in ["where", "when"]]):
        sentence = sentence_answer(sentence, answer)
    elif any([sentence.startswith(elem) for elem in ["is there"]]):
        for old_tok, new_tok in [("is there any", f"{answer} is"), ("is there", f"{answer} is")]:
            sentence = sentence.replace(old_tok, new_tok)
    else:
        sentence = f"{sentence} {init_answer}"
    return sentence


def get_relations(uttr_batch, thres=0.5):
    relations_pred_batch = []
    input_batch = list(zip(*itertools.product(uttr_batch, relations_all)))
    rels_scores = rel_ranker(*input_batch)
    rels_scores = np.array(rels_scores).reshape((len(uttr_batch), len(relations_all), 2))
    for curr_scores in rels_scores:
        pred_rels = []
        rels_with_scores = [
            (curr_score[1], curr_rel)
            for curr_score, curr_rel in zip(curr_scores, relations_all)
            if curr_score[1] > thres
        ]
        for rel_group in rel_groups_list:
            pred_rel_group = [
                (curr_score, curr_rel) for curr_score, curr_rel in rels_with_scores if curr_rel in rel_group
            ]
            if len(pred_rel_group) == 1:
                pred_rel = pred_rel_group[0][1]
                pred_rels.append(pred_rel)
            elif len(pred_rel_group) >= 2:
                pred_rel = max(pred_rel_group)[1]
                pred_rels.append(pred_rel)
        relations_pred_batch.append(pred_rels or [""])
    logger.debug(f"rel clf raw output: {relations_pred_batch}")
    return relations_pred_batch


def postprocess_triplets(triplets_init, scores_init, uttr):
    triplets, existing_obj = [], []
    scores_dict = {}
    for triplet_init, score in zip(triplets_init, scores_init):
        triplet = ""
        fnd = re.findall(r"<subj> (.*?)<rel> (.*?)<obj> (.*)", triplet_init)
        if fnd and fnd[0][1] in rel_type_dict:
            triplet = list(fnd[0])
            if triplet[0] in ["i", "my"]:
                triplet[0] = "user"
            obj = triplet[2]
            if obj in existing_obj:
                prev_triplet, prev_score = scores_dict[obj]
                if score > prev_score:
                    triplets.remove(prev_triplet)
                else:
                    continue
            scores_dict[obj] = (triplet, score)
            existing_obj.append(obj)
            if obj.islower() and obj.capitalize() in uttr:
                triplet[2] = obj.capitalize()
        triplets.append(triplet)
    return triplets


def generate_triplets(uttr_batch, relations_pred_batch):
    triplets_corr_batch = []
    t5_input_uttrs = []
    for uttr, preds in zip(uttr_batch, relations_pred_batch):
        uttrs_mult = [uttr for _ in preds]
        t5_input_uttrs.extend(uttrs_mult)
    relations_pred_flat = list(itertools.chain(*relations_pred_batch))
    t5_pred_triplets, t5_pred_scores = generative_ie(t5_input_uttrs, relations_pred_flat)
    logger.debug(f"t5 raw output: {t5_pred_triplets} scores: {t5_pred_scores}")

    offset_start = 0
    for uttr, pred_rels in zip(uttr_batch, relations_pred_batch):
        rels_len = len(pred_rels)
        triplets_init = t5_pred_triplets[offset_start : (offset_start + rels_len)]
        scores_init = t5_pred_scores[offset_start : (offset_start + rels_len)]
        offset_start += rels_len
        triplets = postprocess_triplets(triplets_init, scores_init, uttr)
        triplets_corr_batch.append(triplets)
    return triplets_corr_batch


def get_result(request):
    st_time = time.time()
    init_uttrs = request.json.get("utterances", [])
    named_entities_batch = request.json.get("named_entities", [[] for _ in init_uttrs])
    entities_with_labels_batch = request.json.get("entities_with_labels", [[] for _ in init_uttrs])
    entity_info_batch = request.json.get("entity_info", [[] for _ in init_uttrs])
    logger.info(
        f"init_uttrs {init_uttrs} entities_with_labels: {entities_with_labels_batch} entity_info: {entity_info_batch}"
    )

    if not init_uttrs:
        triplets_batch = [[""]]
        uttrs = [""]
    elif isinstance(init_uttrs[0], str):
        uttrs = []
        for uttr_list in init_uttrs:
            if len(uttr_list) == 1:
                uttrs.append(uttr_list[0].lower())
            else:
                utt_prev = uttr_list[-2]
                utt_prev_sentences = nltk.sent_tokenize(utt_prev)
                utt_prev = utt_prev_sentences[-1]
                utt_cur = uttr_list[-1]
                utt_prev_l = utt_prev.lower()
                utt_cur_l = utt_cur.lower()
                is_q = (
                    any([utt_prev_l.startswith(q_word) for q_word in ["what ", "who ", "when ", "where "]])
                    or "?" in utt_prev_l
                )

                is_sentence = False
                parsed_sentence = nlp(utt_cur_l)
                if parsed_sentence:
                    tokens = [elem.text for elem in parsed_sentence]
                    tags = [elem.tag_ for elem in parsed_sentence]
                    found_verbs = any([tag in tags for tag in ["VB", "VBZ", "VBP", "VBD"]])
                    if found_verbs and len(tokens) > 2:
                        is_sentence = True

                logger.info(f"is_q: {is_q} --- is_s: {is_sentence} --- utt_prev: {utt_prev_l} --- utt_cur: {utt_cur_l}")
                if is_q and not is_sentence:
                    uttrs.append(sentrewrite(utt_prev_l, utt_cur_l))
                else:
                    uttrs.append(utt_cur_l)
        logger.info(f"input utterances: {uttrs}")
        relations_pred = get_relations(uttrs)
        triplets_batch = generate_triplets(uttrs, relations_pred)
        #relations_pred = get_relations(init_uttrs)
        #triplets_batch = generate_triplets(init_uttrs, relations_pred)
    else:
        uttrs = [" ".join(utt_list) for utt_list in init_uttrs]
        triplets_batch = []
        for uttrs_list in init_uttrs:
            relations_pred = get_relations(uttrs_list)
            curr_triplets_batch = generate_triplets(uttrs_list, relations_pred)
            flattened_triplets = list(itertools.chain(*curr_triplets_batch))
            triplets_batch.append(flattened_triplets)

    logger.info(f"triplets_batch {triplets_batch}")
    triplets_info_batch = []
    for triplets, uttr, named_entities, entities_with_labels, entity_info_list in zip(
        triplets_batch, uttrs, named_entities_batch, entities_with_labels_batch, entity_info_batch
    ):
        uttr = uttr.lower()
        entity_substr_dict = {}
        formatted_triplets, per_triplets = [], []
        if len(uttr.split()) > 2:
            for triplet in triplets:
                if triplet:
                    for entity in entities_with_labels:
                        entity_substr = entity.get("text", "")
                        offsets = entity.get("offsets", [])
                        if not offsets:
                            start_offset = uttr.find(entity_substr.lower())
                            end_offset = start_offset + len(entity_substr)
                            offsets = [start_offset, end_offset]
                        if entity_substr in [triplet[0], triplet[2]]:
                            entity_substr_dict[entity_substr] = {"offsets": offsets}

                    for entity_info in entity_info_list:
                        entity_substr = entity_info.get("entity_substr", "")
                        if (
                            entity_substr in [triplet[0], triplet[2]]
                            or stemmer.stem(entity_substr) in [triplet[0], triplet[2]]
                            and "entity_ids" in entity_info
                        ):
                            if entity_substr not in entity_substr_dict:
                                entity_substr_dict[entity_substr] = {}
                            entity_substr_dict[entity_substr]["entity_ids"] = entity_info["entity_ids"]
                            entity_substr_dict[entity_substr]["dbpedia_types"] = entity_info.get("dbpedia_types", [])
                            entity_substr_dict[entity_substr]["finegrained_types"] = entity_info.get(
                                "entity_id_tags", []
                            )
                    named_entities_list = [entity for elem in named_entities for entity in elem]
                    per_entities = [entity for entity in named_entities_list if entity.get("type", "") == "PER"]
                    if triplet[1] in {"have pet", "have family", "have sibling", "have chidren"} and per_entities:
                        per_triplet = {
                            "subject": triplet[2],
                            "property": "name",
                            "object": per_entities[0].get("text", ""),
                        }
                        per_triplets.append(per_triplet)

                    formatted_triplet = {
                        "subject": triplet[0],
                        rel_type_dict[triplet[1]]: triplet[1],
                        "object": triplet[2],
                    }
                    formatted_triplets.append(formatted_triplet)
        triplets_info_list = []
        if add_entity_info:
            triplets_info_list.append({"triplets": formatted_triplets, "entity_info": entity_substr_dict})
        else:
            triplets_info_list.append({"triplets": formatted_triplets})
        if per_triplets:
            per_entity_info = [{per_triplet["object"]: {"entity_id_tags": ["PER"]}} for per_triplet in per_triplets]
            if add_entity_info:
                triplets_info_list.append({"per_triplets": per_triplets, "entity_info": per_entity_info})
            else:
                triplets_info_list.append({"per_triplet": per_triplets})
        triplets_info_batch.append(triplets_info_list)
    total_time = time.time() - st_time
    logger.info(f"property extraction exec time: {total_time: .3f}s")
    return triplets_info_batch


@app.route("/respond", methods=["POST"])
def respond():
    result = get_result(request)
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
