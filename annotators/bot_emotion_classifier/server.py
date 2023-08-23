import logging
from flask import Flask, request, jsonify
import os
import sentry_sdk
from healthcheck import HealthCheck
from sentry_sdk.integrations.flask import FlaskIntegration

import stanza
# stanza.download('en')
nlp = stanza.Pipeline('en')


pos_type_expl = {'i - someone': 1,
                 'you - someone': 2,
                 'i - you': 3,
                 'you - you': 3,
                 'i - i': 4,
                 'you - i': 5,
                 'we - someone': 6,
                 'someone - someone': 6,
                 'we - we': 7}

neg_type_expl = {'i - you': 1,
                 'i - someone': 2,
                 'we - someone': 3,
                 'you - someone': 3,
                 'you - i': 4,
                 'i - i': 5,
                 'we - we': 5}

first_prons = ['i', 'me', 'myself']
second_prons = ['you']
inclusive_prons = ['we']


def find_root(sent):
    for token in sent:
        if token['deprel'] == 'root':
            return token


def find_clause_head(root, sent):
    clauses = ['ccomp', 'xcomp', 'acl', 'acl:relcl', 'advcl']
    all_clause_heads = []
    head_id = root['id']
    for token in sent:
        if token['head'] == head_id and token['deprel'] in clauses:
            all_clause_heads.append(token)
    return all_clause_heads


def find_arguments(head, sent):
    objects = ['obl', 'obj', 'iobj']
    head_id = head['id']
    subj = ''
    obj = ''
    for token in sent:
        if token['head'] == head_id and 'subj' in token['deprel']:
            subj = token
        elif token['head'] == head_id and token['deprel'] in objects:
            obj = token
    return subj, obj


def reverse_if_not_verb(root, subj, obj, has_clauses):
    not_verbs = ['NOUN', 'ADJ', 'ADV']
    if has_clauses:
        return subj, obj
    if root['upos'] in not_verbs:
        obj = subj
        subj = 'I'
    return subj, obj


def find_final_arguments(sent):
    root = find_root(sent)
    subj, obj = find_arguments(root, sent)
    next_clause_heads = find_clause_head(root, sent)
    has_clauses = False
    if next_clause_heads:
        has_clauses = True
    queue = next_clause_heads

    if subj and not obj:
        dep_subj, dep_obj = '', ''
        while not dep_subj and not dep_obj and queue:
            root = queue[0]
            queue = queue[1:]
            dep_subj, dep_obj = find_arguments(root, sent)
            next_clause_heads = find_clause_head(root, sent)
            queue.extend(next_clause_heads)
        if dep_subj:
            obj = dep_subj
        else:
            obj = {'text': 'someone'}
        return reverse_if_not_verb(root, subj['text'], obj['text'], has_clauses)

    while not subj and not obj and queue:
        root = queue[0]
        queue = queue[1:]
        subj, obj = find_arguments(root, sent)
        next_clause_heads = find_clause_head(root, sent)
        queue.extend(next_clause_heads)

    if obj and not subj:
        if 'Mood=Imp' in root['feats']:
            subj = {'text': 'you'}
        else:
            subj = {'text': 'someone'}
        return reverse_if_not_verb(root, subj['text'], obj['text'], has_clauses)
    elif not subj and not obj:
        subj = {'text': 'someone'}
        obj = {'text': 'someone'}
        return reverse_if_not_verb(root, subj['text'], obj['text'], has_clauses)
    elif subj and obj:
        return subj['text'], obj['text']
    else:
        obj = {'text': 'someone'}
        return subj['text'], obj['text']


def get_dsript_type(orig_sent, type_expl):
    doc = nlp(orig_sent)
    sent = doc.sentences[0].to_dict()
    subj, obj = find_final_arguments(sent)
    subj = subj.lower()
    obj = obj.lower()
    if subj not in first_prons and subj not in second_prons and subj not in inclusive_prons:
        subj = 'someone'
    if obj not in first_prons and obj not in second_prons and obj not in inclusive_prons:
        obj = 'someone'
    if subj in first_prons:
        subj = 'i'
    if obj in first_prons:
        obj = 'i'
    line = subj + ' - ' + obj
    if line not in type_expl:
        type_num = 3
    else:
        type_num = type_expl[line]
    return type_num

sentry_sdk.init(os.getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

positive_emotions = ['admiration', 'joy', 'liking', 'love', 'hope', 'gratitude', 'pride', 'relief', 'surprise']
negative_emotions = ['anger', 'resentment', 'disappointment', 'disliking', 'shame', 'distress', 'fear', 'remorse', 'surprise']


def get_pad_emotions(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        text = f.read()
    lines = text.split('\n')[:-1]
    pad_emotions = {}
    for line in lines:
        parts = line.split('\t')
        pad_dict = [float(dim) for dim in parts[1:]]
        pad_emotions[parts[0]] = pad_dict
    return pad_emotions


def get_reaction_dict(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        text = f.read()
    types = text.split('\n\n')
    full_dict = {}
    for i, t in enumerate(types):
        type_dict = {}
        lines = t.split('\n')
        for line in lines:
            parts = line.split('\t')
            type_dict[parts[0]] = parts[1]
        full_dict[i+1] = type_dict
    return full_dict


pad_emotions = get_pad_emotions('info_files/PAD_emotions.txt')
neg_reactions = get_reaction_dict('info_files/neg_reactions.txt')
pos_reactions = get_reaction_dict('info_files/pos_reactions.txt')

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

pleasure = 0.21 * extraversion + 0.59 * agreeableness + 0.19 * neuroticism
arousal = 0.15 * openness + 0.3 * agreeableness - 0.57 * neuroticism
dominance = 0.25 * openness + 0.17 * conscientiousness + 0.6 * extraversion - 0.32 * agreeableness

default_mood = [pleasure, arousal, dominance]


def get_bot_emotion(sent, emotion):
    if emotion == 'neutral':
        bot_emotion = 'neutral'
    elif emotion == 'surprise':
        # sentiment = get_sentiment(sent)
        sentiment = 'positive'
        if sentiment == 'negative':
            type_num = get_dsript_type(sent, neg_type_expl)
            bot_emotion = neg_reactions[type_num][emotion]
        elif sentiment == 'positive':
            type_num = get_dsript_type(sent, pos_type_expl)
            bot_emotion = pos_reactions[type_num][emotion]
        else:
            bot_emotion = 'neutral'
    elif emotion in negative_emotions:
        type_num = get_dsript_type(sent, neg_type_expl)
        bot_emotion = neg_reactions[type_num][emotion]
    else:
        type_num = get_dsript_type(sent, pos_type_expl)
        bot_emotion = pos_reactions[type_num][emotion]
    return bot_emotion


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
    print(curr_mood, new_mood)
    for i in range(len(curr_mood)):
        if curr_mood[i]*new_mood[i] < 0:
            return False
    return True


def get_new_mood(default_mood, curr_mood, bot_emotion):
    if check_same_mood(pad_emotions[bot_emotion], curr_mood):
        decay = [0, 0, 0]
    else:
        decay = get_decay(default_mood, curr_mood)
    vec = [pad_emotions[bot_emotion][i] - curr_mood[i] for i in range(len(curr_mood))]
    new_mood = [0.5 * curr_mood[i] + 0.5 * vec[i] + decay[i] for i in range(len(curr_mood))]
    new_mood_reg = [1 if dim > 1 else dim for dim in new_mood]
    new_mood_reg = [-1 if dim < -1 else dim for dim in new_mood_reg]

    # dim_symbols = [str(int(dim / abs(dim))) if dim != 0 else '-1' for dim in new_mood_reg]
    # octant = ''.join(dim_symbols)
    # print('New mood:', pad_moods[octant])
    return new_mood_reg


@app.route("/model", methods=["POST"])
def respond():
    sentences = request.json["sentences"]
    bot_mood_list = request.json["bot_mood"]
    user_emotion_list = request.json["user_emotion"]

    print('SENTENCES:', sentences)
    print('BOT MOOD: ', bot_mood_list)
    print('USER_EMOTION: ', user_emotion_list)

    logger.info('User emotion: {}'.format(user_emotion_list[0]))
    logger.info('Current bot mood: {}'.format(bot_mood_list[0]))
    for sent, bot_mood, user_emotion in zip(sentences, bot_mood_list, user_emotion_list):
        logger.info("User's utterance: {}".format(sent[0]))
        bot_emotion = get_bot_emotion(sent[0], user_emotion)
        logger.info('New bot emotion: {}'.format(bot_emotion))
        curr_mood = get_new_mood(default_mood, bot_mood, bot_emotion)
    logger.info('New bot mood: {}'.format(curr_mood))

    # curr_mood = [1, 2, 3]

    # for dim in curr_mood:
    #     if dim != 0:
    #         str(int(dim / abs(dim)))
    #     else:
    #         '-1'

    dim_symbols = [str(int(dim / abs(dim))) if dim != 0 else '-1' for dim in curr_mood]
    octant = ''.join(dim_symbols)
    logger.info('New bot mood label: {}'.format(pad_moods[octant]))
    print('CURRENT MOOD: ', curr_mood)
    return jsonify([{"bot_mood": curr_mood}])


try:
    logger.info("bot-emotion-classifier is starting")
    sent = ['I do not think you are right.']

    bot_emotion = get_bot_emotion(sent[0], 'anger')

    # logger.info("Current bot emotion: {}".format(bot_emotion))
    # logger.info("PAD: {}".format(pad_emotions[bot_emotion]))

    curr_mood = get_new_mood(default_mood, pad_emotions['anger'], bot_emotion)
    
    logger.info("bot-emotion-classifier is ready")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)