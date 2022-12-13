# Copyright 2017 Neural Networks and Deep Learning lab, MIPT
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import os
import time
from collections import defaultdict

from cp_data_store import store
from cp_index_map.index_map import compose_map, make_map_from_spans
from flask import Flask, jsonify, request
from healthcheck import HealthCheck
from label_errors import _get_opcodes, classify_changes, predict_corrections

SERVICE_NAME = os.getenv("SERVICE_NAME", "gector")
SERVICE_PORT = int(os.getenv("SERVICE_PORT", 2102))
STORE_DATA_ENABLE = bool(os.getenv("STORE_DATA_ENABLE", False))
INPUT_DATA_FILE = "server_input_data.jsonl"
print(f"SERVICE_NAME = {SERVICE_NAME}", flush=True)
print(f"SERVICE_PORT = {SERVICE_PORT}", flush=True)
print(f"STORE_DATA_ENABLE = {STORE_DATA_ENABLE}", flush=True)
print(f"INPUT_DATA_FILE = {INPUT_DATA_FILE}", flush=True)


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


app = Flask(__name__)
health = HealthCheck(app, "/healthcheck")

# clear old file
# store.rm_file(INPUT_DATA_FILE)

subject_name = "английский"


def handler(instance):
    if instance["instance_info"]["subject"] not in ["eng"]:
        return {"selections": []}
    orig_essay = instance["annotations"]["basic_reader"]["standard_markup"]["text"]
    orig_sentences = instance["annotations"]["basic_reader"]["extended_markup"]["clear_essay_sentences"]
    orig_offsets = instance["annotations"]["basic_reader"]["extended_markup"]["clear_essay_word_offsets"]
    # здесь contraction_corrector -- скилл, исполняемый непосредственно перед Гектором
    # потом это станет спеллер
    curr_sentences = instance["annotations"]["contraction_corrector"]["essay_sentences"]
    corrections, corrected_sents, index_maps = [], [], []
    for i, curr_paragraph in enumerate(curr_sentences):
        if not curr_paragraph:
            corrected_sents.append([])
            index_maps.append([])
            continue
        corrected_paragraph_sents, paragraph_index_maps = [], []
        orig_paragraph = orig_sentences[i]
        corr_sents = predict_corrections(curr_paragraph)  # skill_sents
        for j, (orig_sent, curr_sent, corr_sent) in enumerate(zip(orig_paragraph, curr_paragraph, corr_sents)):
            curr_index_map = instance["annotations"]["contraction_corrector"]["index_map"][i][j]
            word_offsets = orig_offsets[i][j]
            word_lengths = list(map(len, orig_sentences[i][j]["words"]))
            word_bounds = [(o, o + l) for o, l in zip(word_offsets, word_lengths)]
            # word_offsets.append((word_offsets[-1][1], word_offsets[-1][1]))
            opcodes, _, corr_words = _get_opcodes(curr_sent["words"], corr_sent)  # skill_sent
            new_opcodes = opcodes[:]
            # собираем отображения индексов
            curr_corr_map_data = [(elem[1], elem[2][1] - elem[2][0]) for elem in opcodes]
            curr_corr_index_map = make_map_from_spans(curr_corr_map_data, len(curr_sent["words"]))
            orig_corr_index_map = compose_map(curr_index_map, curr_corr_index_map)
            for elem in new_opcodes:
                # приводим к индексам оригинального предложения
                start, end = elem[1]
                start, end = curr_index_map[start], curr_index_map[end]
                if elem[0] == "replace" and start == end:
                    end = start + 1
                elem[1], elem[3] = (start, end), orig_sent["words"][start:end]
                # расширяем исправления до всех слов, получившихся из одного исходного
                change_start, change_end = elem[2]
                while change_start > 0 and orig_corr_index_map[change_start - 1] == start:
                    change_start -= 1
                while change_end < len(orig_corr_index_map) and orig_corr_index_map[change_end] < end:
                    change_end += 1
                elem[2], elem[4] = (change_start, change_end), corr_words[change_start:change_end]
            # сохраняем ответы
            corrections.extend(classify_changes(new_opcodes, orig_sent["text"], corr_sent, word_bounds, orig_essay))
            corrected_paragraph_sents.append({"text": corr_sent, "words": corr_words})
            paragraph_index_maps.append(orig_corr_index_map)
        corrected_sents.append(corrected_paragraph_sents)
        index_maps.append(paragraph_index_maps)
    repeats = defaultdict(list)
    for i, correction in enumerate(corrections):
        correction["id"] = i
        if correction["subtype"]:
            repeats[(correction["type"], correction["subtype"])].append(i)
    for (t, st), idx in repeats.items():
        if len(idx) > 1:
            for _id in idx:
                corrections[_id]["tag"] = st
    return {"selections": corrections, "corrected_sentences_gector": corrected_sents, "index_map": index_maps}


@app.route("/model", methods=["POST"])
def respond():
    """A handler of requests.
    To use:
    curl -X POST "http://localhost:${PORT}/model" \
    -H "accept: application/json"  -H "Content-Type: application/json" \
    -d "{ \"args\": [ \"data\" ]}"
    """
    st_time = time.time()

    if STORE_DATA_ENABLE:
        store.save2json_line(request.json, INPUT_DATA_FILE)

    responses = [handler(instance) for instance in request.json["input_data"]]

    total_time = time.time() - st_time
    logger.info(f"{SERVICE_NAME} exec time: {total_time:.3f}s")
    return jsonify(responses)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=3000)
