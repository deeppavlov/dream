import requests
import yaml
from api import API, APIKeys, ASRConfig, TTSConfig
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse, JSONResponse
from pathlib import Path


app = FastAPI()
config = yaml.safe_load(Path("configuration.yaml").read_text())

asr_config = ASRConfig(**config["asr"])
tts_config = TTSConfig(**config["tts"])
api_keys = APIKeys(**config["api"])
api = API(api_keys=api_keys)


@app.post("/asr")
async def infer_asr(user_id: str, file: UploadFile = File(...)) -> JSONResponse:
    transcript = api.speech_to_text_v1([file.file], asr_config)
    print(f'transcription is "{transcript}"')
    post_response = requests.post("http://agent:4242", json={"user_id": user_id, "payload": transcript})
    response_payload = post_response.json()
    return JSONResponse(content=response_payload, headers={"transcript": transcript})


@app.post("/tts")
async def infer_tts(response: str) -> StreamingResponse:
    audio_response = api.text_to_speech([response], tts_config)
    return StreamingResponse(audio_response, media_type=f"audio/{tts_config.format}")
