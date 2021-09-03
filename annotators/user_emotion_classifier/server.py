from transformers import BertTokenizer
from .GoEmotions.model import BertForMultiLabelClassification
from .GoEmotions.multilabel_pipeline import MultiLabelPipeline
import numpy as np

import logging
from flask import Flask, request, jsonify
import os
import sentry_sdk


tokenizer = BertTokenizer.from_pretrained("monologg/bert-base-cased-goemotions-original")
model = BertForMultiLabelClassification.from_pretrained("monologg/bert-base-cased-goemotions-original")

sentry_sdk.init(os.getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

goemotions_to_occ = {'admiration': 'admiration', 'amusement': 'joy',
                     'anger': 'anger', 'annoyance': 'anger',
                     'approval': 'liking', 'caring': 'love',
                     'confusion': 'resentment', 'curiosity': 'neutral',
                     'desire': 'hope', 'disappointment': 'disappointment',
                     'disapproval': 'disliking', 'disgust': 'disliking',
                     'embarrassment': 'shame', 'excitement': 'joy',
                     'fear': 'fear', 'gratitude': 'gratitude',
                     'grief': 'distress', 'joy': 'joy',
                     'love': 'love', 'nervousness': 'fear',
                     'optimism': 'hope', 'pride': 'pride',
                     'realization': 'neutral', 'relief': 'relief',
                     'remorse': 'remorse', 'sadness': 'distress',
                     'surprise': 'surprise', 'neutral': 'neutral'
}


@app.route("/model", methods=["POST"])
def respond():
    sentences = request.json['sentences']
    logger.info('User emotion classifier started')
    goemotions = MultiLabelPipeline(
        model=model,
        tokenizer=tokenizer,
        threshold=0.3
    )

    ans = goemotions([sentences[0]])  # there is always only one sentence?
    max_ind = np.argmax(ans[0]['scores'])
    emotion = ans[0]['labels'][max_ind]
    occ_emotion = goemotions_to_occ[emotion]
    logger.info('User emotion classifier finished')
    logger.info(occ_emotion)
    logger.info(jsonify([occ_emotion]))
    return jsonify([occ_emotion])
