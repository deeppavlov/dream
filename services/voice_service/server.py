import logging
import os
import shutil
import time
import requests
import soundfile as sf

import sentry_sdk
from aux_files.inference import infer
from flask import Flask, request, jsonify
from urllib.request import urlopen, URLopener
from sentry_sdk.integrations.flask import FlaskIntegration

CAP_ERR_MSG = "The audiofile format is not supported"
INFERENCE_DIR = "/src/aux_files/data/clotho_audio_files/"
INFERENCE_PARAMS = {
    'dataset_rootdir': '/src/aux_files/data',
    'features_output_dir': '/src/aux_files/data/clotho_dataset',
    'pretrained_pickles_dir': '/src/aux_files/wavetransformer/outputs',
    'pretrained_models_dir': '/src/aux_files/wavetransformer/data',
}

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])

SERVICE_PORT = int(os.getenv("SERVICE_PORT"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
logging.getLogger("werkzeug").setLevel("WARNING")

@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()

    path = request.json.get("sound_path")
    duration = request.json.get("sound_duration")
    type = request.json.get("sound_type")

    logger.info(f"path: {path}")
    logger.info(f"strpath: {str(path)}")

    filename_extract = path[0]
    filename_split = filename_extract[::-1]
    filename_els = filename_split.split("=")
    filename = filename_els[-1]

    logger.info(f"dot split -1: {filename.split('.')[-1]}, filename: {filename}")
    if filename.split('.')[-1] == '.oga':
        file = URLopener()
        file.retrieve(path[0], os.path.join(INFERENCE_DIR, filename))
        data, rate = sf.read(os.path.join(INFERENCE_DIR, filename))
        sf.write(os.path.join(INFERENCE_DIR, filename[:-4] + ".wav"), data, rate)
        captions = infer(INFERENCE_PARAMS)
        responses = [{"sound_type": type, "sound_duration": duration, "sound_path": path, "captions": captions}]
    else:
        responses = [{"sound_type": type, "sound_duration": duration, "sound_path": path, "captions": CAP_ERR_MSG}]

    logger.info(f"VOICE_SERVICE RESPONSE: {responses}")

    total_time = time.time() - st_time
    logger.info(f"voice_service exec time: {total_time:.3f}s")
    return jsonify(responses)