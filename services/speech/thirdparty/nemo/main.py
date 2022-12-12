import requests

from fastapi import FastAPI, File, UploadFile

# from num2words import num2words

app = FastAPI()
# asr = build_model("asr.json")
# tts = build_model("tts.json")


# @app.post("/asr")
# async def infer_asr(user_id: str, file: UploadFile = File(...)):
#     transcript = asr([file.file])[0]
#     print(f'transcription is "{transcript}"')
#     post_response = requests.post("http://agent:4242", json={"user_id": user_id, "payload": transcript})
#     response_payload = post_response.json()
#     response = response_payload["response"]
#     print(f'response is "{response}"')
#     response = re.sub(r"([0-9]+)", lambda x: num2words(x.group(0)), response)
#     response_payload["response"] = response
#     return JSONResponse(content=response_payload, headers={"transcript": transcript})


# @app.post("/tts")
# async def infer_tts(text: str):
#     response = re.sub(r"([0-9]+)", lambda x: num2words(x.group(0)), text)
#     print(f'response is "{response}"')
#     audio_response = tts([response])[0]
#     return StreamingResponse(audio_response, media_type="audio/x-wav")


def synthesize(folder_id, api_key, text):
    url = "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize"
    headers = {
        "Authorization": "Api-Key " + api_key,
    }

    data = {"text": text, "lang": "ru-RU", "voice": "filipp", "folderId": folder_id}

    with requests.post(url, headers=headers, data=data, stream=True) as resp:
        # print("request posted")
        if resp.status_code != 200:
            raise RuntimeError("Invalid response received: code: %d, message: %s" % (resp.status_code, resp.text))

        for chunk in resp.iter_content(chunk_size=None):
            # print("chunk returned")
            yield chunk


@app.post("/tts")
async def infer_tts(text: str):
    FOLDER_ID = "b1gami13b761380nb5hb"  # Идентификатор каталога
    API_KEY = "AQVN3XofRyHEW5PJOhBYCiObnGaZNYM8IvAQskdp"  # API-ключ
    audiofile_name = "kill_mankind.ogg"

    with open(audiofile_name, "wb") as f:
        for audio_content in synthesize(FOLDER_ID, API_KEY, text):
            f.write(audio_content)
    return f

    # return StreamingResponse(audio_response, media_type="audio/x-wav")
