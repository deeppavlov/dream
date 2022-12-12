from email.mime import audio
import os
from argparse import ArgumentParser, Namespace
import json, yaml
from api import API, APIKeys, ASRConfig, TTSConfig
from pathlib import Path


def parse_args() -> Namespace:
    parser = ArgumentParser("a parser for the speech kit api")
    parser.add_argument("--audio_filename", type=str, nargs="*", default=[])

    parser.add_argument("--text", type=str, nargs="*", default=[])

    parser.add_argument("--use_flow_setup", action="store_true")

    args = parser.parse_args()
    return args


def single_api_call(args: Namespace):
    config = yaml.safe_load(Path("configuration.yaml").read_text())

    asr_config = ASRConfig(**config["asr"])
    tts_config = TTSConfig(**config["tts"])
    api_keys = APIKeys(**config["api"])
    api = API(api_keys=api_keys)

    if len(args.audio_filename) == 0 and len(args.text) == 0:
        print("no arguments have been passed")
        exit(-1)

    if len(args.audio_filename) > 0 and len(args.text) > 0:
        print("should have only passed either a text or an audio, not both")
        exit(-2)

    if len(args.audio_filename) > 0:
        return api.speech_to_text_v1(args.audio_filename, config=asr_config)

    elif len(args.text) > 0:
        return api.text_to_speech(args.text[0], config=tts_config)

    exit(0)


if __name__ == "__main__":
    args = parse_args()
    single_api_call(args)
