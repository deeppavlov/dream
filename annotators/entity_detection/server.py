import logging
import os
import re
import time

import sentry_sdk
from flask import Flask, jsonify, request
from nltk.corpus import stopwords

from deeppavlov import build_model

sentry_sdk.init(os.getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__)

config_name = os.getenv("CONFIG")
lowercase = int(os.getenv("LOWERCASE", "1"))
finegrained = int(os.getenv("FINEGRAINED", "0"))


def replace_finegrained_tags(tag):
    if tag in {"loc", "city", "country", "county", "river", "us_state", "road"}:
        return "location"
    elif tag in {"per", "musician", "writer", "athlete", "politician", "actor"}:
        return "person"
    else:
        return tag


try:
    entity_detection = build_model(config_name, download=True)
    entity_detection(["What is the capital of Russia?"])
    logger.info("entity detection model is loaded.")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

EVERYTHING_EXCEPT_LETTERS_DIGITALS_AND_SPACE = re.compile(r"[^a-zA-Z0-9 \-&*+]")
DOUBLE_SPACES = re.compile(r"\s+")
stopwords = set(stopwords.words("english"))


def get_result(request, what_to_annotate):
    st_time = time.time()
    last_utts = request.json.get("sentences", [])
    logger.info(f"annotating: {what_to_annotate}, input (the last utterances): {last_utts}")

    utts_list = []
    utts_list_init = []
    utts_nums = []
    last_utt_starts = []
    for n, hist_utt in enumerate(last_utts):
        if isinstance(hist_utt, str):
            hist_utt = [hist_utt]
        if len(hist_utt) > 0:
            last_utt = hist_utt[-1]
            if last_utt and last_utt[-1] not in {".", "!", "?"}:
                last_utt = f"{last_utt}."
            if len(hist_utt) > 1:
                prev_utt = hist_utt[-2]
                if prev_utt and prev_utt[-1] not in {".", "!", "?"}:
                    prev_utt = f"{prev_utt}."
                last_utt_starts.append(len(prev_utt) + 1)
                concat_utt = f"{prev_utt} {last_utt}"
            else:
                last_utt_starts.append(0)
                concat_utt = last_utt
            if lowercase:
                utts_list.append(concat_utt.lower())
            else:
                utts_list.append(concat_utt)
            utts_list_init.append(concat_utt)
            utts_nums.append(n)

    utt_entities_batch = [{} for _ in last_utts]
    utt_entities = {}
    try:
        if utts_list:
            logger.info(f"input {utts_list}")
            (
                entity_substr_batch,
                entity_offsets_batch,
                entity_positions_batch,
                tokens_batch,
                tags_batch,
                finegrained_tags_batch,
                sentences_offsets_batch,
                sentences_batch,
                probas_batch,
                tokens_conf_batch,
            ) = entity_detection(utts_list)
            logger.info(f"entity_substr_batch {entity_substr_batch} finegrained_tags_batch {finegrained_tags_batch}")
            for (
                entity_substr_list,
                tags_list,
                finegrained_tags_list,
                entity_offsets_list,
                last_utt_start,
                uttr,
                num,
            ) in zip(
                entity_substr_batch,
                tags_batch,
                finegrained_tags_batch,
                entity_offsets_batch,
                last_utt_starts,
                utts_list_init,
                utts_nums,
            ):
                utt_entities = {}
                for entity, tag, finegrained_tags, (start_offset, end_offset) in zip(
                    entity_substr_list, tags_list, finegrained_tags_list, entity_offsets_list
                ):
                    entity_init = uttr[start_offset:end_offset]
                    if entity_init.lower() == entity:
                        entity = entity_init
                    if entity.lower() not in stopwords and len(entity) > 2 and start_offset >= last_utt_start:
                        entity = EVERYTHING_EXCEPT_LETTERS_DIGITALS_AND_SPACE.sub(" ", entity)
                        entity = DOUBLE_SPACES.sub(" ", entity).strip()
                        filtered_finegrained_tags = []
                        if finegrained_tags[0][0] > 0.5:
                            tag = finegrained_tags[0][1].lower()
                            conf, finegrained_tag = finegrained_tags[0]
                            filtered_finegrained_tags.append((finegrained_tag.lower(), round(conf, 3)))
                            for finegrained_elem in finegrained_tags[1:]:
                                conf, finegrained_tag = finegrained_elem
                                if conf > 0.2:
                                    filtered_finegrained_tags.append((finegrained_tag.lower(), round(conf, 3)))
                        else:
                            tag = "misc"
                            filtered_finegrained_tags.append(("misc", 1.0))
                        if not finegrained:
                            tag = replace_finegrained_tags(tag)
                        if "entities" in utt_entities:
                            utt_entities["entities"].append(entity)
                            utt_entities["labelled_entities"].append(
                                {
                                    "text": entity,
                                    "label": tag,
                                    "finegrained_label": filtered_finegrained_tags,
                                    "offsets": (start_offset - last_utt_start, end_offset - last_utt_start),
                                }
                            )
                        else:
                            utt_entities["entities"] = [entity]
                            utt_entities["labelled_entities"] = [
                                {
                                    "text": entity,
                                    "label": tag,
                                    "finegrained_label": filtered_finegrained_tags,
                                    "offsets": (start_offset - last_utt_start, end_offset - last_utt_start),
                                }
                            ]

                if utt_entities:
                    utt_entities_batch[num] = utt_entities
        else:
            utt_entities_batch.append({})
    except Exception as e:
        logger.info(f"error in entity detection, {e}")

    total_time = time.time() - st_time
    logger.info(f"entity detection exec time: {total_time: .3f}s")
    logger.info(f"entity_detection, input {last_utts}, output {utt_entities_batch}")
    return utt_entities_batch


@app.route("/respond", methods=["POST"])
def respond():
    result = get_result(request, "user_uttr")
    return jsonify(result)


@app.route("/respond_batch", methods=["POST"])
def respond_batch():
    result = get_result(request, "hypotheses")
    return jsonify([{"batch": result}])


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8103)
