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
    wikipedia = build_model(config_name, download=True)
    whow_page_extractor = build_model("whow_page_extractor.json", download=True)
    logger.info("model loaded")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e


@app.route("/respond", methods=['POST'])
def respond():
    st_time = time.time()
    inp = request.json
    res_batch = [{"wikipedia_content": [], "main_pages": [], "wikihow_content": []}]
    wikipedia_titles_batch = inp.get("wikipedia_titles", [])
    wikihow_titles_batch = inp.get("wikihow_titles", [])
    try:
        if wikipedia_titles_batch:
            page_content_batch, main_pages_batch = wikipedia(wikipedia_titles_batch)
            res_batch = []
            for page_content, main_pages in zip(page_content_batch, main_pages_batch):
                res_batch.append({"wikipedia_content": page_content, "main_pages": main_pages, "wikihow_content": []})
        elif wikihow_titles_batch:
            page_content_batch = whow_page_extractor(wikihow_titles_batch)
            res_batch = []
            for page_content in page_content_batch:
                res_batch.append({"wikipedia_content": [], "main_pages": [], "wikihow_content": page_content})
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
    total_time = time.time() - st_time
    logger.info(f"wikipedia exec time = {total_time:.3f}s")
    return jsonify(res_batch)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
