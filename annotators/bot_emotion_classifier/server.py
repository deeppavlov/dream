import logging
from flask import Flask, request, jsonify
import os
import sentry_sdk
from healthcheck import HealthCheck
from sentry_sdk.integrations.flask import FlaskIntegration
import stanza
from common.utils import get_emotions, get_sentiment


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
health = HealthCheck(app, "/healthcheck")
logging.getLogger("werkzeug").setLevel("WARNING")


# stanza.download('en')  # -> moved to Dockerfile
nlp = stanza.Pipeline("en")


# D-scripts dictionaries
pos_type_expl = {
    "i - someone": 1,
    "you - someone": 2,
    "i - you": 3,
    "you - you": 3,
    "i - i": 4,
    "you - i": 5,
    "we - someone": 6,
    "someone - someone": 6,
    "we - we": 7,
}

neg_type_expl = {
    "i - you": 1,
    "i - someone": 2,
    "we - someone": 3,
    "you - someone": 3,
    "you - i": 4,
    "i - i": 5,
    "we - we": 5,
}

first_prons = ["i", "me", "myself"]
second_prons = ["you"]
inclusive_prons = ["we"]


# SRL - semantic role labelling
def find_root(sent):
    for token in sent:
        if token["deprel"] == "root":
            return token


def find_clause_head(root, sent):
    clauses = ["ccomp", "xcomp", "acl", "acl:relcl", "advcl"]
    all_clause_heads = []
    head_id = root["id"]
    for token in sent:
        if token["head"] == head_id and token["deprel"] in clauses:
            all_clause_heads.append(token)
    return all_clause_heads


def find_arguments(head, sent):
    objects = ["obl", "obj", "iobj"]
    head_id = head["id"]
    subj = ""
    obj = ""
    for token in sent:
        if token["head"] == head_id and "subj" in token["deprel"]:
            subj = token
        elif token["head"] == head_id and token["deprel"] in objects:
            obj = token
    return subj, obj


def reverse_if_not_verb(root, subj, obj, has_clauses):
    not_verbs = ["NOUN", "ADJ", "ADV"]
    if has_clauses:
        return subj, obj
    if root["upos"] in not_verbs:
        obj = subj
        subj = "I"
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
        dep_subj, dep_obj = "", ""
        while not dep_subj and not dep_obj and queue:
            root = queue[0]
            queue = queue[1:]
            dep_subj, dep_obj = find_arguments(root, sent)
            next_clause_heads = find_clause_head(root, sent)
            queue.extend(next_clause_heads)
        if dep_subj:
            obj = dep_subj
        else:
            obj = {"text": "someone"}
        return reverse_if_not_verb(root, subj["text"], obj["text"], has_clauses)

    while not subj and not obj and queue:
        root = queue[0]
        queue = queue[1:]
        subj, obj = find_arguments(root, sent)
        next_clause_heads = find_clause_head(root, sent)
        queue.extend(next_clause_heads)

    if obj and not subj:
        if "Mood=Imp" in root["feats"]:
            subj = {"text": "you"}
        else:
            subj = {"text": "someone"}
        return reverse_if_not_verb(root, subj["text"], obj["text"], has_clauses)
    elif not subj and not obj:
        subj = {"text": "someone"}
        obj = {"text": "someone"}
        return reverse_if_not_verb(root, subj["text"], obj["text"], has_clauses)
    elif subj and obj:
        return subj["text"], obj["text"]
    else:
        obj = {"text": "someone"}
        return subj["text"], obj["text"]


def get_dsript_type(orig_sent, type_expl):
    doc = nlp(orig_sent)
    sent = doc.sentences[0].to_dict()
    subj, obj = find_final_arguments(sent)
    subj = subj.lower()
    obj = obj.lower()
    if subj not in first_prons and subj not in second_prons and subj not in inclusive_prons:
        subj = "someone"
    if obj not in first_prons and obj not in second_prons and obj not in inclusive_prons:
        obj = "someone"
    if subj in first_prons:
        subj = "i"
    if obj in first_prons:
        obj = "i"
    line = subj + " - " + obj
    if line not in type_expl:
        type_num = 3
    else:
        type_num = type_expl[line]
    return type_num


# emotion and mood dictionaries
positive_emotions = [
    "admiration",
    "joy",
    "liking",
    "love",
    "hope",
    "gratitude",
    "pride",
    "relief",
    "surprise",
    "neutral",
]
negative_emotions = [
    "anger",
    "resentment",
    "disappointment",
    "disliking",
    "shame",
    "distress",
    "fear",
    "remorse",
    "surprise",
    "sadness",
    "disgust",
]


def get_pad_emotions(filename):
    with open(filename, "r", encoding="utf-8") as f:
        text = f.read()
    lines = text.split("\n")[:-1]
    pad_emotions = {}
    for line in lines:
        parts = line.split("\t")
        pad_dict = [float(dim) for dim in parts[1:]]
        pad_emotions[parts[0]] = pad_dict
    return pad_emotions


def get_reaction_dict(filename):
    with open(filename, "r", encoding="utf-8") as f:
        text = f.read()
    types = text.split("\n\n")
    full_dict = {}
    for i, t in enumerate(types):
        type_dict = {}
        lines = t.split("\n")
        for line in lines:
            parts = line.split("\t")
            type_dict[parts[0]] = parts[1]
        full_dict[i + 1] = type_dict
    return full_dict


pad_emotions = {
    "anger": [-0.51, 0.59, 0.25],
    "resentment": [-0.2, -0.3, -0.2],
    "disappointment": [-0.3, -0.4, -0.4],
    "disgust": [-0.4, -0.2, 0.1],
    "shame": [-0.3, 0.1, -0.6],
    "distress": [-0.4, 0.2, 0.5],
    "fear": [-0.64, 0.6, 0.43],
    "sadness": [-0.3, 0.1, -0.6],
    "admiration": [0.4, 0.3, -0.24],
    "joy": [0.4, 0.2, 0.1],
    "liking": [0.4, -0.16, -0.24],
    "love": [0.3, 0.1, 0.2],
    "surprise": [0.2, 0.2, -0.1],
    "gratitude": [0.2, 0.5, -0.3],
    "pride": [0.4, 0.3, 0.3],
    "relief": [0.2, -0.3, -0.4],
    "pity": [-0.4, -0.2, -0.5],
    "neutral": [0.0, 0.0, 0.0],
}

neg_reactions = get_reaction_dict("info_files/neg_reactions.txt")
pos_reactions = get_reaction_dict("info_files/pos_reactions.txt")

pad_moods = {
    "111": "happy",
    "11-1": "dependent",
    "-111": "angry",
    "-1-11": "disdainful",
    "-1-1-1": "sad",
    "1-1-1": "docile",
    "1-11": "relaxed",
    "-11-1": "fear",
    "000": "neutral",
}


# default mood
extraversion = 0.89
agreeableness = 0.92
conscientiousness = 0.86
neuroticism = 0.11
openness = 0.23

pleasure = 0.21 * extraversion + 0.59 * agreeableness + 0.19 * neuroticism
arousal = 0.15 * openness + 0.3 * agreeableness - 0.57 * neuroticism
dominance = 0.25 * openness + 0.17 * conscientiousness + 0.6 * extraversion - 0.32 * agreeableness

default_mood = [pleasure, arousal, dominance]


# get bot emotion using user emotion and user utterance
def get_bot_emotion(sent, emotion, sentiment):
    if emotion == "neutral":
        bot_emotion = "neutral"
    elif emotion == "surprise":
        if sentiment == "negative":
            type_num = get_dsript_type(sent, neg_type_expl)
            bot_emotion = neg_reactions[type_num][emotion]
        elif sentiment == "positive":
            type_num = get_dsript_type(sent, pos_type_expl)
            bot_emotion = pos_reactions[type_num][emotion]
        else:
            bot_emotion = "neutral"
    elif emotion in negative_emotions:
        type_num = get_dsript_type(sent, neg_type_expl)
        bot_emotion = neg_reactions[type_num][emotion]
    else:
        type_num = get_dsript_type(sent, pos_type_expl)
        bot_emotion = pos_reactions[type_num][emotion]
    return bot_emotion


# the rate of mood decrease
def get_dim_decay(default_dim, curr_dim):
    p_dif = abs(default_dim - curr_dim)
    if p_dif == 0:
        p_dif = 0.00001
    decay = 1 / p_dif * 0.01
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


# comparison of old and new mood
def check_same_mood(curr_mood, new_mood):
    print(curr_mood, new_mood)
    for i in range(len(curr_mood)):
        if curr_mood[i] * new_mood[i] < 0:
            return False
    return True


# new mood calculation using difference btw current mood and current emotion
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


def get_mood_label(bot_mood):
    octant = ""
    for dim in bot_mood:
        if dim == 0:
            octant += "0"
        elif dim > 0:
            octant += "1"
        else:
            octant += "-1"

    return pad_moods[octant]


@app.route("/model", methods=["POST"])
def respond():
    sentences = request.json.get("sentences", [])
    annotated_utterances = request.json.get("annotated_utterances", [])
    bot_moods = request.json.get("bot_mood", [])

    results = []
    for sentence, annotated_utterance, bot_mood in zip(sentences, annotated_utterances, bot_moods):
        user_emotion = get_emotions(annotated_utterance, probs=False)[0]
        sentiment = get_sentiment(annotated_utterance, probs=False)[0]

        logger.info("User's utterance: {}".format(sentence))
        logger.info("User emotion: {}".format(user_emotion))
        logger.info("Sentiment: {}".format(sentiment))
        logger.info("Old bot mood: {}".format(bot_mood))

        bot_emotion = get_bot_emotion(sentence, user_emotion, sentiment)
        logger.info("New bot emotion: {}".format(bot_emotion))
        print("NEW BOT EMOTION: ", bot_emotion)

        new_bot_mood = get_new_mood(default_mood, bot_mood, bot_emotion)
        logger.info("New bot mood: {}".format(new_bot_mood))
        print("NEW BOT MOOD: ", new_bot_mood)

        new_bot_mood_label = get_mood_label(new_bot_mood)
        logger.info("New bot mood label: {}".format(new_bot_mood_label))
        print("NEW BOT MOOD LABEL: ", new_bot_mood_label)

        current_result = {"bot_mood": new_bot_mood, "bot_mood_label": new_bot_mood_label, "bot_emotion": bot_emotion}

        results.append(current_result)

    return jsonify(results)


try:
    logger.info("bot-emotion-classifier is starting")

    sentence = "I am so sad"
    user_emotion = "distress"
    sentiment = "negative"
    bot_mood = default_mood

    logger.info("User's utterance: {}".format(sentence))
    logger.info("User emotion: {}".format(user_emotion))
    logger.info("Sentiment: {}".format(sentiment))
    logger.info("Old bot mood: {}".format(bot_mood))

    bot_emotion = get_bot_emotion(sentence, user_emotion, sentiment)
    logger.info("New bot emotion: {}".format(bot_emotion))

    new_bot_mood = get_new_mood(default_mood, bot_mood, bot_emotion)
    logger.info("New bot mood: {}".format(new_bot_mood))

    new_bot_mood_label = get_mood_label(new_bot_mood)
    logger.info("New bot mood label: {}".format(new_bot_mood_label))

    logger.info("bot-emotion-classifier is ready")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
