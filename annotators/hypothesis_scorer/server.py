import logging
import time
import os
import sentry_sdk
from flask import Flask, request, jsonify

sentry_sdk.init(os.getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

try:
    import score
except Exception as e:
    logger.exception("Scorer not loaded")
    sentry_sdk.capture_exception(e)
    raise e


@app.route("/batch_model", methods=["POST"])
def batch_respond():
    st_time = time.time()
    dialogues = request.json.get("dialogues", [])
    try:
        responses = score.predict(dialogues)
    except Exception as e:
        responses = [[0] * len(x.get("hyp", [])) for x in dialogues]
        sentry_sdk.capture_exception(e)
        logger.exception(e)

    logging.info(f"response_selection exec time {time.time() - st_time}")
    return jsonify([{"batch": responses}])


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
