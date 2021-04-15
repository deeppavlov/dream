import logging
import os
import time
from flask import Flask, request, jsonify
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from deeppavlov import build_model

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
sentry_sdk.init(dsn=os.getenv('SENTRY_DSN'), integrations=[FlaskIntegration()])

app = Flask(__name__)

config_name = os.getenv("CONFIG")

try:
    el = build_model(config_name, download=True)
    logger.info("model loaded")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e


@app.route("/model", methods=['POST'])
def respond():
    st_time = time.time()
    inp = request.json
    entity_substr_batch = inp.get("entity_substr", [[""]])
    template_batch = inp.get("template", [""])
    context_batch = inp.get("context", [[""]])
    new_context_batch = []
    for entity_substr_list, context_list in zip(entity_substr_batch, context_batch):
        last_utt = context_list[-1]
        if len(last_utt) > 1 and any([entity_substr.lower() == last_utt.lower()
                                      for entity_substr in entity_substr_list]) or \
                any([entity_substr.lower() == last_utt[:-1] for entity_substr in entity_substr_list]):
            new_context_batch.append(" ".join(context_list))
        else:
            new_context_batch.append(last_utt)

    entity_info_batch = [[{}] for _ in entity_substr_batch]
    try:
        entity_ids_batch, conf_batch, entity_pages_batch = el(entity_substr_batch, template_batch, new_context_batch)
        entity_info_batch = []
        for entity_substr_list, entity_ids_list, conf_list, entity_pages_list in \
                zip(entity_substr_batch, entity_ids_batch, conf_batch, entity_pages_batch):
            entity_info_list = []
            for entity_substr, entity_ids, conf, entity_pages in \
                    zip(entity_substr_list, entity_ids_list, conf_list, entity_pages_list):
                entity_info = {}
                entity_info["entity_substr"] = entity_substr
                entity_info["entity_ids"] = entity_ids
                entity_info["confidences"] = [float(elem) for elem in conf]
                entity_info["entity_pages"] = entity_pages
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
