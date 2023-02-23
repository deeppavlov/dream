import copy
import logging
import os
import re
import time

import nltk
import sentry_sdk
import spacy
from flask import Flask, jsonify, request

from deeppavlov import build_model
from src.sentence_answer import sentence_answer

sentry_sdk.init(os.getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__)

stemmer = nltk.PorterStemmer()
nlp = spacy.load("en_core_web_sm")

config_name = os.getenv("CONFIG")
rel_cls_flag = int(os.getenv("REL_CLS_FLAG", "0"))
add_entity_info = int(os.getenv("ADD_ENTITY_INFO", "0"))

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


def sentrewrite(sentence, init_answer):
    answer = init_answer.strip(".")
    if any([sentence.startswith(elem) for elem in ["what's", "what is"]]):
        for old_tok, new_tok in [
            ("what's your", f"{answer} is my"),
            ("what is your", f"{answer} is my"),
            ("what is", "{answer} is"),
            ("what's", "{answer} is"),
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


def get_result(request):
    st_time = time.time()
    init_uttrs = request.json.get("utterances", [])
    init_uttrs_cased = request.json.get("utterances_init", [])
    if not init_uttrs_cased:
        init_uttrs_cased = copy.deepcopy(init_uttrs)
    named_entities_batch = request.json.get("named_entities", [[] for _ in init_uttrs])
    entities_with_labels_batch = request.json.get("entities_with_labels", [[] for _ in init_uttrs])
    entity_info_batch = request.json.get("entity_info", [[] for _ in init_uttrs])
    logger.info(f"init_uttrs {init_uttrs}")
    uttrs, uttrs_cased = [], []
    for uttr_list, uttr_list_cased in zip(init_uttrs, init_uttrs_cased):
        if len(uttr_list) == 1:
            uttrs.append(uttr_list[0])
            uttrs_cased.append(uttr_list[0])
        else:
            utt_prev = uttr_list_cased[-2]
            utt_prev_sentences = nltk.sent_tokenize(utt_prev)
            utt_prev = utt_prev_sentences[-1]
            utt_cur = uttr_list_cased[-1]
            utt_prev_l = utt_prev.lower()
            utt_cur_l = utt_cur.lower()
            is_q = (
                any([utt_prev_l.startswith(q_word) for q_word in ["what ", "who ", "when ", "where "]])
                or "?" in utt_prev_l
            )

            is_sentence = False
            parsed_sentence = nlp(utt_cur)
            if parsed_sentence:
                tokens = [elem.text for elem in parsed_sentence]
                tags = [elem.tag_ for elem in parsed_sentence]
                found_verbs = any([tag in tags for tag in ["VB", "VBZ", "VBP", "VBD"]])
                if found_verbs and len(tokens) > 2:
                    is_sentence = True

            logger.info(f"is_q: {is_q} --- is_s: {is_sentence} --- utt_prev: {utt_prev_l} --- utt_cur: {utt_cur_l}")
            if is_q and not is_sentence:
                if len(utt_cur_l.split()) <= 2:
                    uttrs.append(sentrewrite(utt_prev_l, utt_cur_l))
                    uttrs_cased.append(sentrewrite(utt_prev, utt_cur))
                else:
                    uttrs.append(f"{utt_prev_l} {utt_cur_l}")
                    uttrs_cased.append(f"{utt_prev} {utt_cur}")
            else:
                uttrs.append(utt_cur_l)
                uttrs_cased.append(utt_cur)

    logger.info(f"input utterances: {uttrs}")
    triplets_batch = []
    outputs, scores = generative_ie(uttrs)
    for output, uttr in zip(outputs, uttrs_cased):
        triplet = ""
        fnd = re.findall(r"<subj> (.*?)<rel> (.*?)<obj> (.*)", output)
        if fnd:
            triplet = list(fnd[0])
            if triplet[0] == "i":
                triplet[0] = "user"
            obj = triplet[2]
            if obj.islower() and obj.capitalize() in uttr:
                triplet[2] = obj.capitalize()
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
    for triplet, uttr, named_entities, entities_with_labels, entity_info_list in zip(
        triplets_batch, uttrs, named_entities_batch, entities_with_labels_batch, entity_info_batch
    ):
        uttr = uttr.lower()
        entity_substr_dict = {}
        formatted_triplet, per_triplet = {}, {}
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
            named_entities_list = []
            for elem in named_entities:
                for entity in elem:
                    named_entities_list.append(entity)
            per_entities = [entity for entity in named_entities_list if entity.get("type", "") == "PER"]
            if triplet[1] in {"have pet", "have family", "have sibling", "have chidren"} and per_entities:
                per_triplet = {"subject": triplet[2], "property": "name", "object": per_entities[0].get("text", "")}

        triplets_info_list = []
        if add_entity_info:
            triplets_info_list.append({"triplet": formatted_triplet, "entity_info": entity_substr_dict})
        else:
            triplets_info_list.append({"triplet": formatted_triplet})
        if per_triplet:
            if add_entity_info:
                triplets_info_list.append(
                    {"triplet": per_triplet, "entity_info": {per_triplet["object"]: {"entity_id_tags": ["PER"]}}}
                )
            else:
                triplets_info_list.append({"triplet": per_triplet})
        triplets_info_batch.append(triplets_info_list)
    total_time = time.time() - st_time
    logger.info(f"property extraction exec time: {total_time: .3f}s")
    logger.info(f"property extraction, input {uttrs}, output {triplets_info_batch} scores {scores}")
    return triplets_info_batch


@app.route("/respond", methods=["POST"])
def respond():
    result = get_result(request)
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8103)
