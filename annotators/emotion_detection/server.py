import logging
import os
import opensmile
import torch
import numpy as np
import sentry_sdk
import cv2
import sys

sys.path.append("/data")
sys.path.append("/data/multimodal_concat")

from multimodal_concat.models import MultimodalClassificationModel, MainModel
from multimodal_concat.utils import prepare_models

from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from transformers import AutoTokenizer, AutoProcessor
from typing import List
from urllib.request import urlretrieve

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))

label2id = {
    "anger": 0,
    "disgust": 1,
    "fear": 2,
    "joy": 3,
    "neutral": 4,
    "sadness": 5,
    "surprise": 6,
}
num_labels = 7
text_model, video_model, audio_model = prepare_models(num_labels, os.getenv("MODEL_PATH"))

logger = logging.getLogger(__name__)


def sample_frame_indices(seg_len, clip_len=16, frame_sample_rate=4, mode="video"):
    converted_len = int(clip_len * frame_sample_rate)
    converted_len = min(converted_len, seg_len - 1)
    end_idx = np.random.randint(converted_len, seg_len)
    start_idx = end_idx - converted_len
    if mode == "video":
        indices = np.linspace(start_idx, end_idx, num=clip_len)
    else:
        indices = np.linspace(start_idx, end_idx, num=clip_len * frame_sample_rate)
    indices = np.clip(indices, start_idx, end_idx - 1).astype(np.int64)
    return indices


def get_frames(
    file_path,
    clip_len=16,
):
    cap = cv2.VideoCapture(file_path)
    v_len = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    indices = sample_frame_indices(v_len)

    frames = []
    for fn in range(v_len):
        success, frame = cap.read()
        if success is False:
            continue
        if fn in indices:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = cv2.resize(frame, dsize=(224, 224), interpolation=cv2.INTER_CUBIC)
            frames.append(res)
    cap.release()

    if len(frames) < clip_len:
        add_num = clip_len - len(frames)
        frames_to_add = [frames[-1]] * add_num
        frames.extend(frames_to_add)

    return frames


def create_final_model():
    multi_model = MultimodalClassificationModel(
        text_model,
        video_model,
        audio_model,
        num_labels,
        input_size=4885,
        hidden_size=512,
    )
    checkpoint = torch.load(os.getenv("MULTIMODAL_MODEL"))
    multi_model.load_state_dict(checkpoint)

    device = "cuda"
    return MainModel(multi_model, device=device)


def process_text(input_tokens: str):
    text_model_name = os.getenv("TEXT_PRETRAINED")
    logger.info(f"{text_model_name}")
    tokenizer = AutoTokenizer.from_pretrained(text_model_name)

    return tokenizer(
        input_tokens,
        padding="max_length",
        truncation=True,
        max_length=128,
        return_tensors="pt",
    )


def process_video(video_path: str):
    video_frames = get_frames(video_path)

    video_model_name = os.getenv("VIDEO_PRETRAINED")
    video_feature_extractor = AutoProcessor.from_pretrained(video_model_name)

    return video_feature_extractor(videos=video_frames, return_tensors="pt")


def process_audio(file_path: str):
    smile = opensmile.Smile(
        opensmile.FeatureSet.ComParE_2016,
        opensmile.FeatureLevel.Functionals,
        sampling_rate=16000,
        resample=True,
        num_workers=5,
        verbose=True,
    )

    redundant_features = os.getenv("REDUNDANT_FEATURES")
    with open(redundant_features, "r") as features_file:
        redundant_features_list = features_file.read().split(",")

    audio_features = smile.process_files([file_path])
    audio_features = audio_features.drop(columns=redundant_features_list, inplace=False)
    return audio_features.values.reshape(audio_features.shape[0], 1, audio_features.shape[1])


def inference(text: str, video_path: str):
    text_encoding = process_text(text)
    video_encoding = process_video(video_path)
    audio_features = process_audio(video_path)
    batch = {
        "text": text_encoding,
        "video": video_encoding,
        "audio": audio_features,
        "label": None,
    }
    label = final_model(batch)
    id2label = {v: k for k, v in label2id.items()}
    return id2label[int(label.detach().cpu())]


def predict_emotion(text: str, video_path: str):
    try:
        logger.warning(f"{inference(text, video_path)}")
        return inference(text, video_path)
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise e


final_model = create_final_model()


class EmotionsPayload(BaseModel):
    personality: List[str]
    video_path: List[str]


def subinfer(msg_text: str, video_path: str):
    emotion = "Emotion detection unsuccessfull. An error occured during inference."
    filepath = "undefined"
    try:
        filename = video_path.split("=")[-1]
        filepath = f"/data/{filename}"
        urlretrieve(video_path, filepath)
        if not os.path.exists(filepath):
            raise ValueError(f"Failed to retrieve videofile from {filepath}")
        emotion = predict_emotion(msg_text + " ", filepath)
        logger.info(f"Detected emotion: {jsonable_encoder(emotion)}")
    except Exception as e:
        raise ValueError(f"The message format is correct, but: {e}")

    return emotion


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/model")
def infer(payload: EmotionsPayload):
    logger.info(f"Emotion Detection: {payload}")
    emotion = [subinfer(p[0], p[1]) for p in zip(payload.personality, payload.video_path)]
    return jsonable_encoder(emotion)
