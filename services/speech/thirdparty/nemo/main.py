import re

import requests
from deeppavlov import build_model
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse, JSONResponse
from num2words import num2words

app = FastAPI()
asr = build_model("asr.json")
tts = build_model("tts.json")


@app.post("/asr")
async def infer_asr(user_id: str, file: UploadFile = File(...)):
    transcript = asr([file.file])[0]
    print(f'transcription is "{transcript}"')
    post_response = requests.post("http://agent:4242", json={"user_id": user_id, "payload": transcript})
    response_payload = post_response.json()
    response = response_payload["response"]
    print(f'response is "{response}"')
    response = re.sub(r"([0-9]+)", lambda x: num2words(x.group(0)), response)
    response_payload["response"] = response
    return JSONResponse(content=response_payload, headers={"transcript": transcript})


@app.post("/tts")
async def infer_tts(text: str):
    response = re.sub(r"([0-9]+)", lambda x: num2words(x.group(0)), text)
    print(f'response is "{response}"')
    audio_response = tts([response])[0]
    return StreamingResponse(audio_response, media_type="audio/x-wav")
