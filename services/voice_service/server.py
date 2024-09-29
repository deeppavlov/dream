import logging
import os
import time
import json
import sys
from itertools import zip_longest

sys.path.append("/src/")
sys.path.append("/src/AudioCaption/")
sys.path.append("/src/AudioCaption/captioning/")
sys.path.append("/src/AudioCaption/captioning/pytorch_runners/")

import sentry_sdk
from AudioCaption.captioning.pytorch_runners.inference_waveform import inference
from flask import Flask, request, jsonify
from urllib.request import URLopener
from sentry_sdk.integrations.flask import FlaskIntegration

CAP_ERR_MSG = "The audiofile format is not supported"
AUDIO_DIR = "/src/audio_input/"
MODEL_PATH = "/src/AudioCaption/clotho_cntrstv_cnn14rnn_trm/swa.pth"

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
        logger.info(f"Processing batch at sound_annotator: {path}, {duration}, {atype}")
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

            logger.info(f"ffmpegging .{filename.split('.')[-1]} to .wav")

            process = subprocess.run(
                [
                    "ffmpeg",
                    "-i",
                    os.path.join(AUDIO_DIR, filename),
                    os.path.join(AUDIO_DIR, filename[: -len(filename.split(".")[-1])] + "wav"),
                ]
            )

            logger.info("ffmpegging finished successfully")
            if process.returncode != 0:
                raise Exception("Something went wrong")
        try:
            logger.info(f"Scanning AUDIO_DIR ({AUDIO_DIR}) for wav files...")
            fname = "NOFILE"
            for i in os.listdir(AUDIO_DIR):
                if i.split(".")[-1] == "wav":
                    logger.info(f"found file: {os.path.join(AUDIO_DIR, i)}")
                    inference(os.path.join(AUDIO_DIR, i), "/src/output.json", MODEL_PATH)
                    fname = i
                    break
            else:
                CAP_ERR_MSG = "No files for inference found in AUDIO_DIR"
                raise Exception(CAP_ERR_MSG)
            logger.info("Inference finished successfully")
            with open('/src/output.json', 'r') as file:
                caption = json.load(file)[fname]
            responses += [{"sound_type": atype, "sound_duration": duration, "sound_path": path, "caption": caption}]
        except Exception as e:
            logger.info(f"An error occurred in voice-service: {CAP_ERR_MSG}, {e}")
            responses.append(
                [{"sound_type": atype, "sound_duration": duration, "sound_path": path, "caption": "Error"}]
            )

    logger.info(f"VOICE_SERVICE RESPONSE: {responses}")

    total_time = time.time() - st_time
    logger.info(f"voice_service exec time: {total_time:.3f}s")
    return jsonify(responses)