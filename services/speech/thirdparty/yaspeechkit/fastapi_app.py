import requests
import yaml
from api import API, APIKeys, ASRConfig, TTSConfig
from base64 import b64encode
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import StreamingResponse, JSONResponse, Response
from pathlib import Path


config = yaml.safe_load(Path("configuration.yaml").read_text())

asr_config = ASRConfig(**config["asr"])
tts_config = TTSConfig(**config["tts"])
api_keys = APIKeys(**config["api"])
api = API(api_keys=api_keys)

app = FastAPI()


@app.post("/")
def default_h() -> Response:
    print("success")


@app.post("/asr")
def infer_asr(user_id: str, file: UploadFile = File(None)) -> JSONResponse:
    # ASR example:
    """
    ```Bash
        curl -X POST "http://localhost:6969/asr?user_id=sknc"  -F 'file=@path/to/your/file.ogg'
    ```
    ```
    # don't forget to
        nc -l 4242
    ```
    to get the actual string
    ```Python
        russian_string = b64decode(response, 'utf8').decode('utf-8')
    ```

    """
    transcript = api.speech_to_text_v1([file.file], asr_config)["text_result"][0]
    post_response = requests.post(
        "http://0.0.0.0:4242",
        json={"user_id": user_id, "payload": b64encode(transcript.encode("utf-8")).decode()},
    )
    post_response.content
    response_payload = post_response.json()
    return JSONResponse(
        content=response_payload, headers={"transcript": b64encode(transcript.encode("utf-8")).decode()}
    )


@app.post("/tts")
async def infer_tts(response: str = Form(...)) -> StreamingResponse:
    # TTS example:
    """
    ```Bash
        curl -X POST "http://localhost:6969/tts" -F "response='Меня зовут Саша'"  --output out.ogg
    ```
    """
    audio_response = api.text_to_speech(response, tts_config)
    return StreamingResponse(audio_response, media_type=f"audio/{tts_config.format}")
