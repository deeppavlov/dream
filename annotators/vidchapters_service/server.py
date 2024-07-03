import logging
import os
import time
from itertools import zip_longest

import sentry_sdk
from flask import Flask, request, jsonify
from urllib.request import URLopener
from sentry_sdk.integrations.flask import FlaskIntegration

import whisper
import whisperx
import pickle 

import argparse

import torch
import numpy as np
import random

import ffmpeg
import clip
import subprocess
import re

import sys

# Добавление пути к sys.path
# sys.path.append(os.path.join(os.path.dirname(__file__), 'src/aux_files/VidChapters'))
sys.path.append('src/aux_files/VidChapters')
from args import get_args_parser

# from aux_files.demo_vid2seq import
from model.vid2seq import _get_tokenizer, Vid2Seq

CAP_ERR_MSG = "The file format is not supported"
CHECKPOINTS = "/src/aux_files/checkpoint_vidchapters"
MODEL_PATH = "/src/aux_files/captioning_model.pth"
MODEL_DIR = "/src/aux_files/TOFILL"
DATA_DIR = "/src/aux_files/data/video_captioning"
DEVICE='cuda'

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
logging.getLogger("werkzeug").setLevel("WARNING")

class Normalize(object):
    def __init__(self, mean, std):
        self.mean = torch.FloatTensor(mean).view(1, 3, 1, 1)
        self.std = torch.FloatTensor(std).view(1, 3, 1, 1)

    def __call__(self, tensor):
        tensor = (tensor - self.mean) / (self.std + 1e-8)
        return tensor

class Preprocessing(object):
    def __init__(self):
        self.norm = Normalize(
            mean=[0.48145466, 0.4578275, 0.40821073],
            std=[0.26862954, 0.26130258, 0.27577711],
        )

    def __call__(self, tensor):
        tensor = tensor / 255.0
        tensor = self.norm(tensor)
        return tensor

def time_tokenize(x, duration, num_bins, num_text_tokens):
    time_token = int(float((num_bins - 1) * x) / float(duration))
    # assert time_token <= num_bins
    return time_token + num_text_tokens

def build_vid2seq_model(dict_of_args, tokenizer):
    model = Vid2Seq(t5_path=dict_of_args.get('model_name'),
                    num_features=dict_of_args.get('max_feats'),
                    embed_dim=dict_of_args.get('embedding_dim'),
                    depth=dict_of_args.get('depth'),
                    heads=dict_of_args.get('heads'),
                    mlp_dim=dict_of_args.get('mlp_dim'),
                    vis_drop=dict_of_args.get('visual_encoder_dropout'),
                    enc_drop=dict_of_args.get('text_encoder_dropout'),
                    dec_drop=dict_of_args.get('text_decoder_dropout'),
                    tokenizer=tokenizer,
                    num_bins=dict_of_args.get('num_bins'),
                    label_smoothing=dict_of_args.get('label_smoothing'),
                    use_speech=dict_of_args.get('use_speech'),
                    use_video=dict_of_args.get('use_video'))
    return model

def generate_asr(video_path, asr_output_path):

    video_path = '/cephfs/home/dolidze/notebooks/test.webm'
    asr_output_path = '/cephfs/home/dolidze/notebooks/test_asr'
    # device='cuda'

    logger.info("load Whisper model")
    asr_model = whisper.load_model('large-v2', DEVICE, download_root=MODEL_DIR)
    logger.info("extract ASR")
    asr = asr_model.transcribe(video_path)
    logger.info("load align model")
    align_model, metadata = whisperx.load_align_model(language_code=asr['language'], device=DEVICE, model_dir=MODEL_DIR)
    logger.info("extract audio")
    audio = whisperx.load_audio(video_path)
    logger.info("align ASR")
    aligned_asr = whisperx.align(asr["segments"], align_model, metadata, audio, DEVICE, return_char_alignments=False)
    logger.info("saving")
    pickle.dump(aligned_asr, open(asr_output_path, 'wb'))

    return asr_output_path

def generate_video_caption(video_path, asr_path):

    video_path = '/cephfs/home/dolidze/notebooks/test.webm'
    asr_path = '/cephfs/home/dolidze/notebooks/test_asr'

    # reparse parser
    parser = argparse.ArgumentParser(parents=[get_args_parser()])
    args = parser.parse_args()
    cli_string = '--load=<CHECKPOINT> --video_example=<VIDEO_PATH> --asr_example <OUTPUT_ASR_PATH> --combine_datasets chapters --model_name t5-base'
    cli_arguments = cli_string.split()
    args = parser.parse_args(cli_arguments)
    dict_of_args = vars(args)
    dict_of_args['combine_datasets'] = 'chapters'
    dict_of_args['model_name'] = 't5-base'

    device = torch.device(dict_of_args.get('device'))

    # fix seeds
    seed = dict_of_args.get('seed')
    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)

    logger.info("load Vid2Seq model")
    tokenizer = _get_tokenizer(dict_of_args.get('model_name'), dict_of_args.get('num_bins'))
    model = build_vid2seq_model(args, tokenizer)
    model.eval()
    model.to(device)
    # assert args.load
    dict_of_args['load']=CHECKPOINTS
    checkpoint = torch.load(dict_of_args.get('load'), map_location="cpu")
    model.load_state_dict(checkpoint["model"], strict=False)

    logger.info("loading visual backbone")
    preprocess = Preprocessing()
    backbone, _ = clip.load("ViT-L/14", download_root=MODEL_DIR, device=device)
    backbone.eval()
    backbone.to(device)

    logger.info("extracting visual features")
    # TODO: rewrite into sep. function 
    dict_of_args['video_example'] = video_path
    probe = ffmpeg.probe(dict_of_args.get('video_example'))
    video_stream = next((stream for stream in probe["streams"] if stream["codec_type"] == "video"), None)
    
    width = int(video_stream["width"])
    height = int(video_stream["height"])
    num, denum = video_stream["avg_frame_rate"].split("/")
    frame_rate = int(num) / int(denum)
    if height >= width:
        h, w = int(height * 224 / width), 224
    else:
        h, w = 224, int(width * 224 / height)
    assert frame_rate >= 1

    cmd = ffmpeg.input(dict_of_args.get('video_example')).filter("fps", fps=1).filter("scale", w, h)
    x = int((w - 224) / 2.0)
    y = int((h - 224) / 2.0)
    cmd = cmd.crop(x, y, 224, 224)
    out, _ = cmd.output("pipe:", format="rawvideo", pix_fmt="rgb24").run(capture_stdout=True, quiet=True)
    
    h, w = 224, 224
    video = np.frombuffer(out, np.uint8).reshape([-1, h, w, 3])
    video = torch.from_numpy(video.astype("float32"))
    video = video.permute(0, 3, 1, 2)
    video = video.squeeze()
    video = preprocess(video)
    with torch.no_grad():
        video = backbone.encode_image(video.to(device))

    # Subsample or pad visual features
    if len(video) >= dict_of_args.get('max_feats'):
        sampled = []
        for j in range(dict_of_args.get('max_feats')):
            sampled.append(video[(j * len(video)) // dict_of_args.get('max_feats')])
        video = torch.stack(sampled)
        video_len = dict_of_args.get('max_feats')
    else:
        video_len = len(video)
        video = torch.cat([video, torch.zeros(dict_of_args.get('max_feats') - video_len, 768).to(device)], 0)
    video = video.unsqueeze(0).to(device)
    logger.info("visual features extracted")

    logger.info("load ASR")
    dict_of_args['asr_example'] = asr_path
    segments = pickle.load(open(dict_of_args.get('asr_example'), 'rb'))["segments"]
    texts, starts, ends = [], [], []
    for i in range(len(segments)):
        text = segments[i]['text']
        if text.strip():
            texts.append(text)
            starts.append(segments[i]['start'])
            ends.append(segments[i]['end'])
    sub = {'text': texts, 'start': starts, 'end': ends}

    logger.info("ASR to tokens")
    probe = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1',
        dict_of_args.get('video_example')], 
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    duration = float(probe.stdout)
    if not sub['text']:
        input_tokens = (torch.ones(1) * tokenizer.eos_token_id).long()
    else:
        time_input_tokens = [torch.LongTensor([time_tokenize(st, duration, dict_of_args.get('num_bins'), len(tokenizer) - dict_of_args.get('num_bins')),
                                                time_tokenize(ed, duration, dict_of_args.get('num_bins'), len(tokenizer) - dict_of_args.get('num_bins'))])
                            for st, ed in zip(sub['start'], sub['end'])]
        text_input_tokens = [tokenizer(x, add_special_tokens=False, max_length=dict_of_args.get('max_input_tokens'),
                                        padding="do_not_pad", truncation=True, return_tensors="pt",)['input_ids'][0]
                            for x in sub['text']]
        input_tokens = [torch.cat([ti, te], 0) for ti, te in zip(time_input_tokens, text_input_tokens)]
        input_tokens = torch.cat(input_tokens, 0)
        input_tokens = input_tokens[:dict_of_args.get('max_input_tokens') - 1]
        input_tokens = torch.cat([input_tokens, torch.LongTensor([tokenizer.eos_token_id])], 0)
    input_tokens = input_tokens.unsqueeze(0).to(device)
    input_tokenized = {'input_ids': input_tokens,
                        'attention_mask': input_tokens != 0}

    logger.info("forward to Vid2Seq")
    with torch.no_grad():
        output = model.generate(video=video,
                                input_tokenized=input_tokenized,
                                use_nucleus_sampling=dict_of_args.get('num_beams') == 0,
                                num_beams=dict_of_args.get('num_beams'),
                                max_length=dict_of_args.get('max_output_tokens'),
                                min_length=1,
                                top_p=dict_of_args.get('top_p'),
                                repetition_penalty=dict_of_args.get('repetition_penalty'),
                                length_penalty=dict_of_args.get('length_penalty'),
                                num_captions=1,
                                temperature=1)
    
    logger.info("decode results")
    # TODO: rewrite as function
    sequences = re.split(r'(?<!<)\s+(?!>)', output[0])
    indexes = [j for j in range(len(sequences) - 1) if sequences[j][:6] == '<time=' and sequences[j + 1][:6] == '<time=']
    last_processed = -2
    res = []
    for j, idx in enumerate(indexes):
        if idx == last_processed + 1:  # avoid processing 3 time tokens in a row as 2 separate events
            continue
        seq = [sequences[k] for k in range(idx + 2, indexes[j + 1] if j < len(indexes) - 1 else len(sequences)) if sequences[k] != '<time=']
        if seq:
            text = ' '.join(seq)
        else:  # no text
            continue
        start_re = re.search(r'\<time\=(\d+)\>', sequences[idx])
        # assert start_re, sequences[idx]
        start_token = int(start_re.group(1))
        start = float(start_token) * float(duration) / float(dict_of_args.get('num_bins') - 1)
        end_re = re.search(r'\<time\=(\d+)\>', sequences[idx + 1])
        # assert end_re, sequences[idx + 1]
        end_token = int(end_re.group(1))
        end = float(end_token) * float(duration) / float(dict_of_args.get('num_bins') - 1)
        if end <= start:  # invalid time
            continue
        res.append({'sentence': text,
                    'timestamp': [start, end]})
        last_processed = idx

        logger.info(res)

    return res

@app.route("/respond", methods=["POST"])
def respond():
    global CAP_ERR_MSG
    st_time = time.time()

    paths = request.json.get("video_paths")
    durations = request.json.get("video_durations")
    types = request.json.get("video_types")

    responses = []

    for path, duration, atype in zip_longest(paths, durations, types):
        logger.info(f"Processing batch at vidchapters annotator: {path}, {duration}, {atype}")
        filename_els = path.split("=")
        filename = filename_els[-1]

        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)

        for i in os.listdir(DATA_DIR):
            os.remove(os.path.join(DATA_DIR, i))

        if filename.split(".")[-1] in ["oga", "ogg", "mp4", "webm"]:
            file = URLopener()
            file.retrieve(path, os.path.join(DATA_DIR, filename))

            # process = subprocess.run(
            #     [
            #         "ffmpeg",
            #         "-i",
            #         os.path.join(DATA_DIR, filename),
            #         os.path.join(DATA_DIR, filename[: -len(filename.split(".")[-1])] + "wav"),
            #     ]
            # )
            # if process.returncode != 0:
            #     raise Exception("Something went wrong")
        try:
            logger.info(f"Scanning DATA_DIR ({DATA_DIR}) for files...")
            for i in os.listdir(DATA_DIR):
                logger.info(i, i.split(".")[0], i.split(".")[-1])
                logger.info(os.path.join(DATA_DIR, i.split(".")[0]+'_asr'))
                logger.info("Scanning finished successfully, files found, starting inference...")
                break
                # if i.split(".")[-1] == "wav":
                #     break
            else:
                CAP_ERR_MSG = "No files for inference found in DATA_DIR"
                raise Exception(CAP_ERR_MSG)
            
            # caption = infer(AUDIO_DIR, MODEL_PATH)
            asr_output_path = os.path.join(DATA_DIR, i.split(".")[0]+'_asr')
            video_path = os.path.join(DATA_DIR, i)
            asr_caption = generate_asr(video_path, asr_output_path)
            video_caption = generate_video_caption(video_path, asr_caption)
            logger.info("Inference finished successfully")
            responses += [{"video_type": atype, "video_duration": duration, "video_path": path, "asr_path":  asr_caption, "caption": video_caption}]
        except Exception:
            logger.info(f"An error occurred in voice-service: {CAP_ERR_MSG}")
            #TODO: Error on which step asr or vid2seq
            responses.append(
                [{"video_type": atype, "video_duration": duration, "video_path": path, "asr_path":  "Error", "caption": "Error"}]
            )

    logger.info(f"VIDCHAPTERS_SERVICE RESPONSE: {responses}")
    #logger.info(f"VIDCHAPTERS_SERVICE RESPONSE: {CAP_ERR_MSG}")

    total_time = time.time() - st_time
    logger.info(f"service exec time: {total_time:.3f}s")
    return jsonify(responses)