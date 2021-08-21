import logging
import os
import re
import time
from flask import Flask, request, jsonify
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from deeppavlov import build_model

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])

app = Flask(__name__)

config_name = os.getenv("CONFIG")

try:
    el = build_model(config_name, download=True)
    logger.info("model loaded")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

GENRES_TEMPLATE = re.compile(
    r"(\brock\b|heavy metal|\bjazz\b|\bblues\b|\bpop\b|\brap\b|hip hop\btechno\b" r"|dubstep|classic)"
)
SPORT_TEMPLATE = re.compile(r"(soccer|football|basketball|baseball|tennis|mma|boxing|volleyball|chess|swimming)")

genres_dict = {
    "rock": "Q11399",
    "heavy metal": "Q38848",
    "jazz": "Q8341",
    "blues": "Q9759",
    "pop": "Q37073",
    "rap": "Q6010",
    "hip hop": "Q6010",
    "techno": "Q170611",
    "dubstep": "Q20474",
    "classic": "Q9730",
}

sport_dict = {
    "soccer": "Q2736",
    "football": "Q2736",
    "basketball": "Q5372",
    "baseball": "Q5369",
    "tennis": "Q847",
    "mma": "Q114466",
    "boxing": "Q32112",
    "volleyball": "Q1734",
    "chess": "Q718",
    "swimming": "Q31920",
}


def extract_topic_skill_entities(utt, entity_substr_list, entity_ids_list):
    found_substr = ""
    found_id = ""
    found_genres = re.findall(GENRES_TEMPLATE, utt)
    if found_genres:
        genre = found_genres[0]
        genre_id = genres_dict[genre]
        if all([genre not in elem for elem in entity_substr_list]) or all(
            [genre_id not in entity_ids for entity_ids in entity_ids_list]
        ):
            found_substr = genre
            found_id = genre_id
    found_sport = re.findall(SPORT_TEMPLATE, utt)
    if found_sport:
        sport = found_sport[0]
        sport_id = sport_dict[sport]
        if all([sport not in elem for elem in entity_substr_list]) or all(
            [sport_id not in entity_ids for entity_ids in entity_ids_list]
        ):
            found_substr = sport
            found_id = sport_id

    return found_substr, found_id


@app.route("/model", methods=["POST"])
def respond():
    st_time = time.time()
    inp = request.json
    entity_substr_batch = inp.get("entity_substr", [[""]])
    template_batch = inp.get("template", [""])
    context_batch = inp.get("context", [[""]])
    long_context_batch = []
    short_context_batch = []
    for entity_substr_list, context_list in zip(entity_substr_batch, context_batch):
        last_utt = context_list[-1]
        if (
            len(last_utt) > 1
            and any([entity_substr.lower() == last_utt.lower() for entity_substr in entity_substr_list])
            or any([entity_substr.lower() == last_utt[:-1] for entity_substr in entity_substr_list])
        ):
            context = " ".join(context_list)
        else:
            context = last_utt
        if isinstance(context, list):
            context = " ".join(context)
        if isinstance(last_utt, list):
            short_context = " ".join(last_utt)
        else:
            short_context = last_utt
        long_context_batch.append(context)
        short_context_batch.append(short_context)

    entity_types_batch = [[[] for _ in entity_substr_list] for entity_substr_list in entity_substr_batch]
    entity_info_batch = [[{}] for _ in entity_substr_batch]
    try:
        entity_ids_batch, conf_batch, tokens_match_conf_batch, entity_pages_batch, entity_pages_titles_batch = el(
            entity_substr_batch, template_batch, long_context_batch, entity_types_batch, short_context_batch
        )
        entity_info_batch = []
        for (
            entity_substr_list,
            entity_ids_list,
            conf_list,
            tokens_match_conf_list,
            entity_pages_list,
            entity_pages_titles_list,
            context,
        ) in zip(
            entity_substr_batch,
            entity_ids_batch,
            conf_batch,
            tokens_match_conf_batch,
            entity_pages_batch,
            entity_pages_titles_batch,
            short_context_batch,
        ):
            entity_info_list = []
            for entity_substr, entity_ids, conf, tokens_match_conf, entity_pages, entity_pages_titles in zip(
                entity_substr_list,
                entity_ids_list,
                conf_list,
                tokens_match_conf_list,
                entity_pages_list,
                entity_pages_titles_list,
            ):
                entity_info = {}
                entity_info["entity_substr"] = entity_substr
                entity_info["entity_ids"] = entity_ids
                entity_info["confidences"] = [float(elem) for elem in conf]
                entity_info["tokens_match_conf"] = [float(elem) for elem in tokens_match_conf]
                entity_info["entity_pages"] = entity_pages
                entity_info["entity_pages_titles"] = entity_pages_titles
                entity_info_list.append(entity_info)
            topic_substr, topic_id = extract_topic_skill_entities(context, entity_substr_list, entity_ids_list)
            if topic_substr:
                entity_info = {}
                entity_info["entity_substr"] = topic_substr
                entity_info["entity_ids"] = [topic_id]
                entity_info["confidences"] = [float(1.0)]
                entity_info["tokens_match_conf"] = [float(1.0)]
                entity_info_list.append(entity_info)
            entity_info_batch.append(entity_info_list)
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
    total_time = time.time() - st_time
    logger.info(f"entity linking exec time = {total_time:.3f}s")
    return jsonify(entity_info_batch)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
