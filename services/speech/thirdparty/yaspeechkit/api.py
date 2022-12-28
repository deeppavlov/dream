import os
import json
import yaml
import urllib.request
import requests
from dataclasses import dataclass, asdict, fields
from typing import Callable, List, Literal, Dict, Union
import grpc

import sys

def classFromArgs(cls: dataclass, args: dict):
    field_set = {f.name for f in fields(cls) if f.init}
    return cls(**{k : v for k, v in args.items() if k in field_set})


def create_token(oauth_token: str):
    params = {'yandexPassportOauthToken': oauth_token}
    response = requests.post('https://iam.api.cloud.yandex.net/iam/v1/tokens', params=params)                                                   
    decode_response = response.content.decode('UTF-8')
    text = json.loads(decode_response) 
    iam_token = text.get('iamToken')
    expires_iam_token = text.get('expiresAt')
    
    return iam_token, expires_iam_token

@dataclass
class APIKeys:
    folder_id: str
    api_key_secret: str
    
    oauth_token: str


@dataclass
class ASRConfig:
    file_format: Literal["ogg"]
    input_dir: str
    lang: str
    format: Union[Literal["oggopus", "lpcm"], Literal["LINEAR16_PCM", "OGG_OPUS"]]
    numbers_as_words: Union[str, bool]
    sample_rate: int = 48000 #Union[48000, 16000, 8000]
    save_results: Literal["yaml", "json", None] = None
    output_dir: str = "."
    
@dataclass
class TTSConfig:
    output_dir: str
    lang: str
    #https://cloud.yandex.ru/docs/speechkit/tts/voices
    voice: Literal["alena", "filipp", "jane", "zahar", "ermil"]
    format: Literal["oggopus", "lpcm", "mp3"]
    speed: float
    sample_rate: int = 48000 #Union[48000, 16000, 8000]



@dataclass
class API:
    api_keys: APIKeys

    def __post_init__(self):
        #generating iam token
        
        self.iam_token, self.expiration_date = create_token(self.api_keys.oauth_token)
        with open("iam_token.txt", "w") as f:
            f.write(f"IAM token {self.iam_token} expires at {self.expiration_date}")

    def speech_to_text_v1(self, files: List[str], config: ASRConfig) -> Dict[str, List[str]]:
        asr_results = []
        for audiofile_name in files:
            try:    
                data = audiofile_name.read()
            except Exception as e:
                print(
                    f"could not read this file beacuse of exception \n {e}"
                )
                exit(-1)

            params = "&".join([
                f"topic=general",
                f"folderId={self.api_keys.folder_id}",
                f"lang={config.lang}",
                f"specification.audioEncoding={config.format}",
                f"sampleRateHertz={config.sample_rate}",
                f"rawResults={config.numbers_as_words}"
            ])
            url = urllib.request.Request(f"https://stt.api.cloud.yandex.net/speech/v1/stt:recognize?{params}", data=data)
            url.add_header(f"Authorization", f"Api-Key {self.api_keys.api_key_secret}") 

            responseData = urllib.request.urlopen(url).read().decode('UTF-8')
            decoded_data = json.loads(responseData)

            if decoded_data.get("error_code") is None:
                asr_result = decoded_data.get("result")
            else:
                asr_result = 'Nothing has been recognized'
            
            asr_results.append(asr_result)
        
        if len(asr_results) == 0: 
            print("Nothing has been recongnized")

        result = {
                    "text_result": asr_results,
                    "parameters": asdict(config)
                 }

        if config.save_results is not None:
            save_path = os.path.join(config.output_dir, f"result.{config.save_results}")
            if config.save_results == "json":
                with open(save_path, "w", encoding='utf8') as fp:
                    json.dump(result, fp, 
                               ensure_ascii = False)
            elif config.save_results == "yaml":
                with open(save_path, "w") as fp:
                    yaml.safe_dump(result, fp, 
                                   default_flow_style = False, 
                                   allow_unicode = True,
                                   sort_keys = False)
            else: 
                print("Unknow file format: only json and yaml are supported")

        return result

    def speech_to_text_v2(self, audio_file_name: str, config: ASRConfig, chunk_size: int) -> None:
            audio_file_name = os.path.join(config.input_dir, audio_file_name)
            #TODO: how to load responses
            #maybe deprecated for a while
            os.system(
                f"python cloudapi/output_dir/tmp.py --iam_token {self.iam_token} \
                                                    --folder_id {self.api_keys.folder_id} \
                                                    --path {audio_file_name} \
                                                    --chunk_size {chunk_size} \
                                                    --lang {config.lang} \
                                                    --format {config.format} \
                                                    --numbers_as_words {config.numbers_as_words} \
                                                    --sample_rate {config.sample_rate} \
                                                    --output_dir {config.output_dir}"
            )


    def text_to_speech(self, text: str, config: TTSConfig, name_generator: Callable = None) -> List[List[float]]:
        def synthesize():
            url = 'https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize'
            headers = {
                'Authorization': 'Api-Key ' + self.api_keys.api_key_secret,
            }

            data = {
                'text': text,
                'lang': config.lang,
                'voice': config.voice,
                'folderId': self.api_keys.folder_id,
                "format": config.format,
                "speed": config.speed,
                "sampleRateHertz": config.sample_rate
            }

            with requests.post(url, headers = headers, data = data, stream = True) as resp:
                if resp.status_code != 200:
                    raise RuntimeError(f"Invalid response received: code: {resp.status_code}, message: {resp.text}")

                for chunk in resp.iter_content(chunk_size = None):
                    yield chunk
        



        if config.output_dir is not None:
            audio = list()
            for audio_content in synthesize():
                audio.append(audio_content)
            with open(os.path.join(config.output_dir, f"{name_generator()}.{config.format}" ), "wb") as f:
                [f.write(audio_content) for audio_content in audio]

        return synthesize()



