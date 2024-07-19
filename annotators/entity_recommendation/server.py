import urllib.request
import logging
import os
import time
import yaml
from flask import Flask, request, jsonify
import sentry_sdk
import torch
import numpy as np
from src.model_utils.thswad import load_light_model_from_path
from src.utils.misc import to_gpu
from pathlib import Path


def download_model_if_needed(config):
    model_path = Path(config['light_model_path'])
    model_path.parent.mkdir(parents=True, exist_ok=True)
    if not model_path.exists() or ('force_download' in config and config['force_download']):
        urllib.request.urlretrieve(config['light_model_url'], config['light_model_path'])


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
sentry_sdk.init(os.getenv("SENTRY_DSN"))

app = Flask(__name__)

config_name = os.getenv("CONFIG")

try:
    with open(config_name, 'r') as f:
        config = yaml.safe_load(f)
    download_model_if_needed(config)
    PREV_CNT = config['prev_count']
    model = load_light_model_from_path(config['light_model_path'], PREV_CNT)
    logger.info("model loaded")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e


PADDING_VALUE = model.get_padding_value()


def select_entity_ids(el_message, reference):
    if not el_message:
        return None

    entities = []
    for entity in el_message:
        ids = np.array(entity['entity_ids'])
        confidences = np.array(entity['confidences'])
        filter_ids = list(e_id in reference for e_id in ids)
        if not any(filter_ids):
            continue

        entities.append(reference.get(ids[filter_ids][np.argmax(confidences[filter_ids])], PADDING_VALUE))

    return entities


def parse_input(el_results, reference):
    wikidata_results = []
    for dialog in el_results:
        dialog_entities_ids = []
        for message in dialog:
            if not message:
                continue

            for entity_id in select_entity_ids(message, reference):
                dialog_entities_ids.append(entity_id)

        if len(dialog_entities_ids) < PREV_CNT:
            dialog_entities_ids = [PADDING_VALUE] * (PREV_CNT - len(dialog_entities_ids)) + dialog_entities_ids
        elif len(dialog_entities_ids) > PREV_CNT:
            dialog_entities_ids = dialog_entities_ids[len(dialog_entities_ids) - PREV_CNT:]
        wikidata_results.append(dialog_entities_ids)

    return wikidata_results


def make_result(idxs, confs):
    result = {
        'entities': [],
        'confs': [],
    }
    for idx, conf in zip(idxs, confs):
        if idx != PADDING_VALUE:
            result['entities'].append(model.id2entity[idx.item()])
            result['confs'].append(conf.item())
    return result


@app.route("/model", methods=["POST"])
def respond():
    st_time = time.time()
    try:
        ids_prev = to_gpu(torch.LongTensor(parse_input(request.json['entities'], model.entity2id)))
        score = model.evaluate_rec(ids_prev)
        topk = torch.topk(score, config['top_k_count'], dim=1)
        topk_confs = (topk[0] / 100).cpu()
        topk_idxs = topk[1].cpu()
        result = [make_result(idxs, confs) for idxs, confs in zip(topk_idxs, topk_confs)]
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
        result = []

    total_time = time.time() - st_time
    logger.info(f"entity linking exec time = {total_time:.3f}s")
    return jsonify({'entity_recommendation': result})


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8095)
