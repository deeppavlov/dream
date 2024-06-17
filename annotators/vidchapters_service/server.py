import logging
import os
import time
from itertools import zip_longest

import sentry_sdk
from flask import Flask, request, jsonify
from urllib.request import URLopener
from sentry_sdk.integrations.flask import FlaskIntegration

# from aux_files.demo_vid2seq import
from aux_files.VidChapters.model import build_vid2seq_model, _get_tokenizer


import whisper
import whisperx
import pickle 

import numpy as np
import random
import torch

CAP_ERR_MSG = "The file format is not supported"
CHECKPOINTS = "/src/aux_files/checkpoint_vidchapters"
MODEL_PATH = "/src/aux_files/captioning_model.pth"
MODEL_DIR = "/src/aux_files/TOFILL"
DEVICE='cuda'

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
logging.getLogger("werkzeug").setLevel("WARNING")

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

def generate_video_caption(video_path):
    # да начнется шиза!

    # set seed
    seed = 42
    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)


    logger.info("load Vid2Seq model")
    tokenizer = _get_tokenizer(model_name = 't5-base', num_bins = 100)

    # vid2seq_args = t5_path='t5-base',
    #                 num_features=100,
    #                 embed_dim=768,
    #                 depth=12,
    #                 heads=12,
    #                 mlp_dim=2048,
    #                 vis_drop=0.1,
    #                 enc_drop=0.1,
    #                 dec_drop=0.1,
    #                 tokenizer=tokenizer,
    #                 num_bins=100,
    #                 label_smoothing=0.1,
    #                 use_speech=True,
    #                 use_video=True

    model = build_vid2seq_model(vid2seq_args, tokenizer)
    model.eval()
    model.to(DEVICE)

#     checkpoint = torch.load(args.load, map_location="cpu")
# model.load_state_dict(checkpoint["model"], strict=False)

# # Extract video frames from video
# print("loading visual backbone")
# preprocess = Preprocessing()
# backbone, _ = clip.load("ViT-L/14", download_root=MODEL_DIR, device=device)
# backbone.eval()
# backbone.to(device)
# print("extracting visual features")
# probe = ffmpeg.probe(args.video_example)
# video_stream = next(
#     (stream for stream in probe["streams"] if stream["codec_type"] == "video"), None
# )
# width = int(video_stream["width"])
# height = int(video_stream["height"])
# num, denum = video_stream["avg_frame_rate"].split("/")
# frame_rate = int(num) / int(denum)
# if height >= width:
#     h, w = int(height * 224 / width), 224
# else:
#     h, w = 224, int(width * 224 / height)
# assert frame_rate >= 1

# cmd = ffmpeg.input(args.video_example).filter("fps", fps=1).filter("scale", w, h)
# x = int((w - 224) / 2.0)
# y = int((h - 224) / 2.0)
# cmd = cmd.crop(x, y, 224, 224)
# out, _ = cmd.output("pipe:", format="rawvideo", pix_fmt="rgb24").run(
#     capture_stdout=True, quiet=True
# )

# h, w = 224, 224
# video = np.frombuffer(out, np.uint8).reshape([-1, h, w, 3])
# video = torch.from_numpy(video.astype("float32"))
# video = video.permute(0, 3, 1, 2)
# video = video.squeeze()
# video = preprocess(video)
# with torch.no_grad():
#     video = backbone.encode_image(video.to(device))

# # Subsample or pad visual features
# if len(video) >= args.max_feats:
#     sampled = []
#     for j in range(args.max_feats):
#         sampled.append(video[(j * len(video)) // args.max_feats])
#     video = torch.stack(sampled)
#     video_len = args.max_feats
# else:
#     video_len = len(video)
#     video = torch.cat(
#         [video, torch.zeros(args.max_feats - video_len, 768).to(device)], 0
#     )
# video = video.unsqueeze(0).to(device)
# print("visual features extracted")

# # Extract ASR from video
# assert args.asr_example
# print("load ASR")
# segments = pickle.load(open(args.asr_example, 'rb'))["segments"]
# texts, starts, ends = [], [], []
# for i in range(len(segments)):
#     text = segments[i]['text']
#     if text.strip():
#         texts.append(text)
#         starts.append(segments[i]['start'])
#         ends.append(segments[i]['end'])
# sub = {'text': texts,
#        'start': starts,
#        'end': ends}

# # ASR to tokens
# print("ASR to tokens")
# probe = subprocess.run(
#     ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1',
#      args.video_example], stdout=subprocess.PIPE,
#     stderr=subprocess.STDOUT)
# duration = float(probe.stdout)
# if not sub['text']:
#     input_tokens = (torch.ones(1) * tokenizer.eos_token_id).long()
# else:
#     time_input_tokens = [torch.LongTensor([time_tokenize(st, duration, args.num_bins, len(tokenizer) - args.num_bins),
#                                            time_tokenize(ed, duration, args.num_bins, len(tokenizer) - args.num_bins)])
#                          for st, ed in zip(sub['start'], sub['end'])]
#     text_input_tokens = [tokenizer(x, add_special_tokens=False, max_length=args.max_input_tokens,
#                                    padding="do_not_pad", truncation=True, return_tensors="pt",)['input_ids'][0]
#                          for x in sub['text']]
#     input_tokens = [torch.cat([ti, te], 0) for ti, te in zip(time_input_tokens, text_input_tokens)]
#     input_tokens = torch.cat(input_tokens, 0)
#     input_tokens = input_tokens[:args.max_input_tokens - 1]
#     input_tokens = torch.cat([input_tokens, torch.LongTensor([tokenizer.eos_token_id])], 0)
# input_tokens = input_tokens.unsqueeze(0).to(device)
# input_tokenized = {'input_ids': input_tokens,
#                    'attention_mask': input_tokens != 0}

# # Forward to the Vid2Seq model
# print("forward to Vid2Seq")
# with torch.no_grad():
#     output = model.generate(video=video,
#                             input_tokenized=input_tokenized,
#                             use_nucleus_sampling=args.num_beams == 0,
#                             num_beams=args.num_beams,
#                             max_length=args.max_output_tokens,
#                             min_length=1,
#                             top_p=args.top_p,
#                             repetition_penalty=args.repetition_penalty,
#                             length_penalty=args.length_penalty,
#                             num_captions=1,
#                             temperature=1)

# # Decode result
# print("decode results")
# sequences = re.split(r'(?<!<)\s+(?!>)', output[0]) # "<time=5> <time=7> Blablabla <time=7> <time=9> Blobloblo <time=2>" -> ['<time=5>', '<time=7>', 'Blablabla', '<time=7>', '<time=9>', 'Blobloblo', '<time=2>']
# indexes = [j for j in range(len(sequences) - 1) if sequences[j][:6] == '<time=' and sequences[j + 1][:6] == '<time=']
# last_processed = -2
# res = []
# for j, idx in enumerate(indexes):  # iterate on predicted events
#     if idx == last_processed + 1:  # avoid processing 3 time tokens in a row as 2 separate events
#         continue
#     seq = [sequences[k] for k in range(idx + 2, indexes[j + 1] if j < len(indexes) - 1 else len(sequences)) if sequences[k] != '<time=']
#     if seq:
#         text = ' '.join(seq)
#     else:  # no text
#         continue
#     start_re = re.search(r'\<time\=(\d+)\>', sequences[idx])
#     assert start_re, sequences[idx]
#     start_token = int(start_re.group(1))
#     start = float(start_token) * float(duration) / float(args.num_bins - 1)
#     end_re = re.search(r'\<time\=(\d+)\>', sequences[idx + 1])
#     assert end_re, sequences[idx + 1]
#     end_token = int(end_re.group(1))
#     end = float(end_token) * float(duration) / float(args.num_bins - 1)
#     if end <= start:  # invalid time
#         continue
#     res.append({'sentence': text,
#                 'timestamp': [start, end]})
#     last_processed = idx
# print(res)


    return 0

@app.route("/respond", methods=["POST"])
def respond():
    global CAP_ERR_MSG
    st_time = time.time()

    paths = request.json.get("sound_paths")
    paths = request.json.get("video_paths") if all([el is None for el in paths]) else paths
    durations = request.json.get("sound_durations")
    durations = request.json.get("video_durations") if all([el is None for el in durations]) else durations
    types = request.json.get("sound_types", None)
    types = request.json.get("video_types") if all([el is None for el in types]) else types

    responses = []

    for path, duration, atype in zip_longest(paths, durations, types):
        logger.info(f"Processing batch at voice_service: {path}, {duration}, {atype}")
        filename_els = path.split("=")
        filename = filename_els[-1]

        if not os.path.exists(AUDIO_DIR):
            os.makedirs(AUDIO_DIR)

        for i in os.listdir(AUDIO_DIR):
            os.remove(os.path.join(AUDIO_DIR, i))

        if filename.split(".")[-1] in ["oga", "ogg", "mp4"]:
            file = URLopener()
            file.retrieve(path, os.path.join(AUDIO_DIR, filename))

            import subprocess

            process = subprocess.run(
                [
                    "ffmpeg",
                    "-i",
                    os.path.join(AUDIO_DIR, filename),
                    os.path.join(AUDIO_DIR, filename[: -len(filename.split(".")[-1])] + "wav"),
                ]
            )
            if process.returncode != 0:
                raise Exception("Something went wrong")
        try:
            logger.info(f"Scanning AUDIO_DIR ({AUDIO_DIR}) for wav files...")
            for i in os.listdir(AUDIO_DIR):
                if i.split(".")[-1] == "wav":
                    break
            else:
                CAP_ERR_MSG = "No files for inference found in AUDIO_DIR"
                raise Exception(CAP_ERR_MSG)
            logger.info("Scanning finished successfully, files found, starting inference...")
            caption = infer(AUDIO_DIR, MODEL_PATH)
            logger.info("Inference finished successfully")
            responses += [{"sound_type": atype, "sound_duration": duration, "sound_path": path, "caption": caption}]
        except Exception:
            logger.info(f"An error occurred in voice-service: {CAP_ERR_MSG}")
            responses.append(
                [{"sound_type": atype, "sound_duration": duration, "sound_path": path, "caption": "Error"}]
            )

    # logger.info(f"VIDCHAPTERS_SERVICE RESPONSE: {responses}")
    logger.info(f"VIDCHAPTERS_SERVICE RESPONSE: {CAP_ERR_MSG}")

    total_time = time.time() - st_time
    logger.info(f"service exec time: {total_time:.3f}s")
    return "CAP_ERR_MSG"