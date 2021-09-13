import re
import shutil
from logging import getLogger
from pathlib import Path
from tempfile import NamedTemporaryFile

import nemo.collections.asr as nemo_asr

import requests

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from num2words import num2words

app = FastAPI()
logger = getLogger(__file__)
quartznet = nemo_asr.models.EncDecCTCModel.from_pretrained(model_name="QuartzNet15x5Base-En")


def save_upload_file(upload_file: UploadFile, destination: Path) -> None:
    try:
        with destination.open("wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
    finally:
        upload_file.file.close()


def save_upload_file_tmp(upload_file: UploadFile) -> Path:
    try:
        suffix = Path(upload_file.filename).suffix
        with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(upload_file.file, tmp)
            tmp_path = Path(tmp.name)
    finally:
        upload_file.file.close()
    return tmp_path



@app.post("/asr")
async def infer_asr(user_id: str, file: UploadFile = File(...)):
    tmp_path = save_upload_file_tmp(file)
    try:
        transcript = quartznet.transcribe(paths2audio_files=[str(tmp_path)])[0]
    finally:
        tmp_path.unlink()
    logger.info(f'transcription is "{transcript}"')
    post_response = requests.post("http://agent:4242", json={"user_id": user_id, "payload": transcript})
    response_payload = post_response.json()
    response = response_payload["response"]
    logger.info(f'response is "{response}"')
    response = re.sub(r"([0-9]+)", lambda x: num2words(x.group(0)), response)
    response_payload["response"] = response
    return JSONResponse(content=response_payload, headers={"transcript": transcript})


