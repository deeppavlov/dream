import logging
import time
import os
 
from transformers import BertTokenizer, BertForMaskedLM
import torch
from flask import Flask, request, jsonify
from healthcheck import HealthCheck
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
import clip
import os
import torch
from transformers import GPT2Tokenizer
import skimage.io as io
import PIL.Image
from model import ClipCaptionModel, generate_beam, generate2
from pathlib import Path
 
sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])
 
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info('!!!!!!!!!!!!!!!!!' + str(torch.__version__))
dirs = os.listdir('/opt/conda/lib/python3.7/site-packages/data/models/')
for dir in dirs:
    logger.info('?????????' + dir)
#logger.info('????????????????????' + Path(__file__).absolute())
 
D = torch.device
CPU = torch.device('cpu')
 
 
def get_device(device_id: int) -> D:
   if not torch.cuda.is_available():
       return CPU
   device_id = min(torch.cuda.device_count() - 1, device_id)
   return torch.device(f'cuda:{device_id}')
 
 
CUDA = get_device
 
PRETRAINED_MODEL_PATH = os.environ.get("PRETRAINED_MODEL_PATH")
logger.info('!!!!!!!!!!!!!!!!!!!!!!!!' + PRETRAINED_MODEL_PATH)

 
try:
   device = CUDA(0)
 
   clip_model, preprocess = clip.load("ViT-B/32", device=device, jit=False)
   tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
 
   prefix_length = 10
 
   model = ClipCaptionModel(prefix_length)
 
   model.load_state_dict(torch.load('/opt/conda/lib/python3.7/site-packages/data/models/coco_weights.pt', map_location=CPU))
 
   model = model.eval()
   model = model.to(device)
 
   logger.info("image captioning model is ready")
except Exception as e:
   sentry_sdk.capture_exception(e)
   logger.exception(e)
   raise e
 
app = Flask(__name__)
health = HealthCheck(app, "/healthcheck")
logging.getLogger("werkzeug").setLevel("WARNING")
 
 
@app.route("/respond", methods=["POST"])
def respond():
   st_time = time.time()
 
   image_paths = request.json.get("text", [])
   try:
        images = None
        for image_path in image_paths:
            image = io.imread(image_path)
            pil_image = PIL.Image.fromarray(image)
            image = preprocess(pil_image).unsqueeze(0).to(device)
            if images is None:
                images = image
            else:
                images = torch.cat([images, image], dim=0)
        with torch.no_grad():
            prefixes = clip_model.encode_image(images).to(device, dtype=torch.float32)
            prefixes_embed = model.clip_project(prefixes).reshape(len(image_paths), prefix_length, -1)
        use_beam_search = False
        if use_beam_search:
            generated_text_prefixes = generate_beam(model, tokenizer, embed=prefixes_embed)
        else:
            generated_text_prefixes = generate2(model, tokenizer, embeds=prefixes_embed, batch_size=len(image_paths))
   except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        generated_text_prefix = ""
 
   total_time = time.time() - st_time
#    logger.info(generated_text_prefixes[0])
#    logger.info(str(len(generated_text_prefixes)))
   logger.info(f"image_captioning exec time: {total_time:.3f}s")
   return jsonify({"captions": generated_text_prefixes})
