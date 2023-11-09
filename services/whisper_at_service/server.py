import logging
import os
import sys
import time

import sentry_sdk
from aux_files.inference import infer
from flask import Flask, request, jsonify
from urllib.request import urlopen, URLopener
from sentry_sdk.integrations.flask import FlaskIntegration

CAP_ERR_MSG = "The audiofile format is not supported"
AUDIO_DIR = "/whisper_at/data"
MODEL_PATH = "/whisper_at/model.pth"

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

    path = request.json.get("sound_path")
    duration = request.json.get("sound_duration")
    type = request.json.get("sound_type")

    logger.info(f"path: {path}")

    filename_extract = path[0]
    filename_els = filename_extract.split("=")
    filename = filename_els[-1]

    if not os.path.exists(AUDIO_DIR):
        os.makedirs(AUDIO_DIR)

    for i in os.listdir(AUDIO_DIR):
        os.remove(os.path.join(AUDIO_DIR, i))

    if filename.split('.')[-1] in ['oga', 'mp3', 'MP3', 'ogg', 'flac', 'mp4']:
        file = URLopener()
        file.retrieve(path[0], os.path.join(AUDIO_DIR, filename))

        import subprocess
        process = subprocess.run(['ffmpeg', '-i', os.path.join(AUDIO_DIR, filename), os.path.join(AUDIO_DIR, filename[:-len(filename.split('.')[-1])] + "wav")])
        if process.returncode != 0:
            raise Exception("Something went wrong")
    # try:
    logger.info(f"Scanning AUDIO_DIR ({AUDIO_DIR}) for wav files...")
    for i in os.listdir(AUDIO_DIR):
        if i.split(".")[-1] == 'wav':
            break
    else:
        CAP_ERR_MSG = "No files for inference found in AUDIO_DIR"
        raise Exception(CAP_ERR_MSG)
    logger.info("Scanning finished successfully, files found, starting inference...")
    captions = infer(AUDIO_DIR, MODEL_PATH)
    logger.info("Inference finished successfully")
    responses = [{"sound_type": type, "sound_duration": duration, "sound_path": path, "captions": captions}]
    # except:
    #     responses = [{"sound_type": type, "sound_duration": duration, "sound_path": path, "captions": CAP_ERR_MSG}]

    logger.info(f"WHISPER_SERVICE RESPONSE: {responses}")

    total_time = time.time() - st_time
    # logger.info(f"voice_service exec time: {total_time:.3f}s")
    return jsonify(responses)