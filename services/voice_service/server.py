import logging
import os
import time
from itertools import zip_longest

import sentry_sdk
from aux_files.inference import infer
from flask import Flask, request, jsonify
from urllib.request import URLopener
from sentry_sdk.integrations.flask import FlaskIntegration

CAP_ERR_MSG = "The audiofile format is not supported"
AUDIO_DIR = "/src/aux_files/data/clotho_audio_files/"
MODEL_PATH = "/src/aux_files/AudioCaption/experiments/clotho_v2/train_val/TransformerModel/cnn14rnn_trm/seed_1/swa.pth"

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])

SERVICE_PORT = int(os.getenv("SERVICE_PORT"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
logging.getLogger("werkzeug").setLevel("WARNING")


@app.route("/respond", methods=["POST"])
def respond():
    global CAP_ERR_MSG
    st_time = time.time()

    paths = request.json.get("sound_paths")
    paths = request.json.get("video_paths") if all([el is None for el in paths]) else paths
    durations = request.json.get("sound_durations")
    durations = request.json.get("video_durations") if all([el is None for el in durations]) else durations
    types = request.json.get("sound_types", None)
    types = request.json.get("video_types") if all([el is None for el in types]) else types

    responses = []

    for path, duration, atype in zip_longest(paths, durations, types):
        logger.info(f"Processing batch at voice_service: {path}, {duration}, {atype}")
        filename_els = path.split("=")
        filename = filename_els[-1]

        if not os.path.exists(AUDIO_DIR):
            os.makedirs(AUDIO_DIR)

        for i in os.listdir(AUDIO_DIR):
            os.remove(os.path.join(AUDIO_DIR, i))

        if filename.split(".")[-1] in ["oga", "mp3", "MP3", "ogg", "flac", "mp4"]:
            file = URLopener()
            file.retrieve(path, os.path.join(AUDIO_DIR, filename))

            import subprocess

            process = subprocess.run(
                [
                    "ffmpeg",
                    "-i",
                    os.path.join(AUDIO_DIR, filename),
                    os.path.join(AUDIO_DIR, filename[: -len(filename.split(".")[-1])] + "wav"),
                ]
            )
            if process.returncode != 0:
                raise Exception("Something went wrong")
        try:
            logger.info(f"Scanning AUDIO_DIR ({AUDIO_DIR}) for wav files...")
            for i in os.listdir(AUDIO_DIR):
                if i.split(".")[-1] == "wav":
                    break
            else:
                CAP_ERR_MSG = "No files for inference found in AUDIO_DIR"
                raise Exception(CAP_ERR_MSG)
            logger.info("Scanning finished successfully, files found, starting inference...")
            caption = infer(AUDIO_DIR, MODEL_PATH)
            logger.info("Inference finished successfully")
            responses += [{"sound_type": atype, "sound_duration": duration, "sound_path": path, "caption": caption}]
        except Exception:
            logger.info(f"An error occurred in voice-service: {CAP_ERR_MSG}")
            responses.append(
                [{"sound_type": atype, "sound_duration": duration, "sound_path": path, "caption": "Error"}]
            )

    logger.info(f"VOICE_SERVICE RESPONSE: {responses}")

    total_time = time.time() - st_time
    logger.info(f"voice_service exec time: {total_time:.3f}s")
    return jsonify(responses)
