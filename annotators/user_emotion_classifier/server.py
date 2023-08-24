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

def get_pad_emotions():
    pad_emotions = {
        "anger":          [-0.51, 0.59, 0.25], 
        "resentment":     [-0.2, -0.3, -0.2], 
        "disappointment": [-0.3, -0.4, -0.4], 
        "disliking":      [-0.4, -0.2, 0.1], 
        "shame":          [-0.3, 0.1, -0.6], 
        "distress":       [-0.4, 0.2, 0.5], 
        "fear":           [-0.64, 0.6, 0.43], 
        "remorse":        [-0.3, 0.1, -0.6], 
        "admiration":     [0.4, 0.3, -0.24], 
        "joy":            [0.4, 0.2, 0.1], 
        "liking":         [0.4, -0.16, -0.24], 
        "love":           [0.3, 0.1, 0.2], 
        "hope":           [0.2, 0.2, -0.1], 
        "gratitude":      [0.2, 0.5, -0.3], 
        "pride":          [0.4, 0.3, 0.3], 
        "relief":         [0.2, -0.3, -0.4], 
        "pity":           [-0.4, -0.2, -0.5], 
        "neutral":        [0., 0., 0.]}

    return pad_emotions
pad_emotions = get_pad_emotions()

pad_moods = {
    '111': 'happy',
    '11-1': 'dependent',
    '-111': 'angry',
    '-1-11': 'disdainful',
    '-1-1-1': 'sad',
    '1-1-1': 'docile',
    '1-11': 'relaxed',
    '-11-1': 'fear',
}

extraversion = 0.89
agreeableness = 0.92
conscientiousness = 0.86
neuroticism = 0.11
openness = 0.23

pleasure = 0.21*extraversion + 0.59*agreeableness + 0.19*neuroticism
arousal = openness*0.23 + 0.3*agreeableness - 0.57*neuroticism
dominance = 0.25*openness + 0.17*conscientiousness + 0.6*extraversion - 0.32*agreeableness

default_mood = [pleasure, arousal, dominance]

def get_dim_decay(default_dim, curr_dim):
    p_dif = abs(default_dim - curr_dim)
    if p_dif == 0:
        p_dif = 0.00001
    decay = 1/p_dif * 0.01
    if decay > p_dif:
        decay = p_dif
    if default_dim < curr_dim:
        decay = -decay
    return decay


def get_decay(default_mood, curr_mood):
    decay = []
    for i in range(len(default_mood)):
        decay.append(get_dim_decay(default_mood[i], curr_mood[i]))
    return decay


def check_same_mood(curr_mood, new_mood):
    for i in range(len(curr_mood)):
        if curr_mood[i]*new_mood[i] < 0:
            return False
    return True


def get_new_mood(default_mood, curr_mood, user_emotion):
    if check_same_mood(pad_emotions[user_emotion], curr_mood):
        decay = [0, 0, 0]
    else:
        decay = get_decay(default_mood, curr_mood)
    vec = [pad_emotions[user_emotion][i] - curr_mood[i] for i in range(len(curr_mood))]
    new_mood = [0.5 * curr_mood[i] + 0.5 * vec[i] + decay[i] for i in range(len(curr_mood))]
    new_mood_reg = [1 if dim > 1 else dim for dim in new_mood]
    new_mood_reg = [-1 if dim < -1 else dim for dim in new_mood_reg]

    # dim_symbols = [str(int(dim / abs(dim))) if dim != 0 else '-1' for dim in new_mood_reg]
    # octant = ''.join(dim_symbols)
    # print('New mood:', pad_moods[octant])
    return new_mood_reg


@app.route("/model", methods=["POST"])
def respond():
    sentences = request.json['sentences']
    user_mood = request.json.get('user_mood', default_mood)
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

    curr_mood = get_new_mood(default_mood, user_mood, occ_emotion)
    dim_symbols = [str(int(dim / abs(dim))) if dim != 0 else '-1' for dim in curr_mood]
    curr_mood_octant = ''.join(dim_symbols)
    

    logger.info('User emotion classifier finished')
    logger.info(occ_emotion)
    logger.info(jsonify([occ_emotion]))
    # logger.info(jsonify([occ_emotion, curr_mood_octant]))
    return jsonify([occ_emotion])
    # return jsonify(jsonify([occ_emotion, curr_mood_octant]))
