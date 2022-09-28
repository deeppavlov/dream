import os

import torch
from torchvision import transforms
import numpy as np
from fairseq import utils
from fairseq import checkpoint_utils

from utils.eval_utils import eval_step
from tasks.mm_tasks.caption import CaptionTask
from fairseq.tasks import register_task
from PIL import Image
import logging
import time
from flask import Flask, request, jsonify
from healthcheck import HealthCheck
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

# Register caption task
register_task("caption", CaptionTask)

# turn on cuda if GPU is available
use_cuda = torch.cuda.is_available()
# use fp16 only when GPU is available
use_fp16 = False

overrides = {
    "bpe_dir": "/ofa/utils/BPE",
    "eval_cider": False,
    "beam": 5,
    "max_len_b": 16,
    "no_repeat_ngram_size": 3,
    "seed": 7,
}

models, cfg, task = checkpoint_utils.load_model_ensemble_and_task(
    utils.split_paths("/opt/conda/lib/python3.7/site-packages/data/models/caption.pt"),
    arg_overrides=overrides,
)

# Move models to GPU
for model in models:
    model.eval()
    if use_fp16:
        model.half()
    if use_cuda and not cfg.distributed_training.pipeline_model_parallel:
        model.cuda()
    model.prepare_for_inference_(cfg)

# Initialize generator
generator = task.build_generator(models, cfg.generation)

# Image transform

mean = [0.5, 0.5, 0.5]
std = [0.5, 0.5, 0.5]

patch_resize_transform = transforms.Compose(
    [
        lambda image: image.convert("RGB"),
        transforms.Resize(
            (cfg.task.patch_image_size, cfg.task.patch_image_size),
            interpolation=Image.BICUBIC,
        ),
        transforms.ToTensor(),
        transforms.Normalize(mean=mean, std=std),
    ]
)

# Text preprocess
bos_item = torch.LongTensor([task.src_dict.bos()])
eos_item = torch.LongTensor([task.src_dict.eos()])
pad_idx = task.src_dict.pad()


def encode_text(text, length=None, append_bos=False, append_eos=False):
    s = task.tgt_dict.encode_line(line=task.bpe.encode(text), add_if_not_exist=False, append_eos=False).long()
    if length is not None:
        s = s[:length]
    if append_bos:
        s = torch.cat([bos_item, s])
    if append_eos:
        s = torch.cat([s, eos_item])
    return s


# Construct input for caption task
def construct_sample(image):
    patch_image = patch_resize_transform(image).unsqueeze(0)
    patch_mask = torch.tensor([True])
    src_text = encode_text(" what does the image describe?", append_bos=True, append_eos=True).unsqueeze(0)
    src_length = torch.LongTensor([s.ne(pad_idx).long().sum() for s in src_text])
    sample = {
        "id": np.array(["42"]),
        "net_input": {
            "src_tokens": src_text,
            "src_lengths": src_length,
            "patch_images": patch_image,
            "patch_masks": patch_mask,
        },
    }
    return sample


# Function to turn FP32 to FP16
def apply_half(t):
    if t.dtype is torch.float32:
        return t.to(dtype=torch.half)
    return t


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
health = HealthCheck(app, "/healthcheck")
logging.getLogger("werkzeug").setLevel("WARNING")


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()

    img_paths = request.json.get("text", [])
    captions = []
    try:
        for img_path in img_paths:
            image = Image.open(img_path)
            image.thumbnail((256, 256))

            # Construct input sample & preprocess for GPU if cuda available
            sample = construct_sample(image)
            sample = utils.move_to_cuda(sample) if use_cuda else sample
            sample = utils.apply_to_sample(apply_half, sample) if use_fp16 else sample

            with torch.no_grad():
                caption, scores = eval_step(task, generator, models, sample)

            captions.append(caption)

    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)

    total_time = time.time() - st_time
    logger.info(f"captioning exec time: {total_time:.3f}s")
    return jsonify({"caption": captions})
