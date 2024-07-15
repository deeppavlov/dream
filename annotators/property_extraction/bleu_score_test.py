import json
from nltk.translate.bleu_score import sentence_bleu
from nltk.tokenize import word_tokenize
import requests

fl = open("/home/korzanova/.deeppavlov/downloads/dialogue_nli/dialogue_nli.json", "r")
data = json.load(fl)

sent2triplets = {}
for d in data["test"]:
    if d[0] not in sent2triplets:
        sent2triplets[d[0]] = []
    sent2triplets[d[0]].append(d[1])


def generate_triplets(uttr_batch):
    triplets_pred = requests.post("http://0.0.0.0:8136/respond", json={"utterances": uttr_batch}).json()
    final_preds = []
    for i in triplets_pred:
        triplets = i[0].get("triplets")
        if triplets:
            cur_preds = []
            for triplet in triplets:
                subj = triplet.get("subject")
                if subj == "user":
                    subj = "i"
                rel = triplet.get("relation")
                if not rel:
                    rel = triplet.get("property")
                obj = triplet.get("object")
                cur_preds.append([subj, rel, obj])
            final_preds.append(cur_preds)
        else:
            final_preds.append([triplets])

    return final_preds


def batch_tokenize(batch):
    return [[word_tokenize(" ".join(triplet)) for triplet in item] for item in batch]


def compute_bleu(golds_batch, pred_batch) -> float:
    overall_score = 0.0
    num_generated_triples = 0.0

    golds_batch = batch_tokenize(golds_batch)
    pred_batch = batch_tokenize(pred_batch)
    for golds, preds in zip(golds_batch, pred_batch):
        if not preds:
            preds = [["<none>"]]
        for pred_tokens in preds:
            overall_score += sentence_bleu(
                references=golds,
                hypothesis=pred_tokens,
                weights=(1, 0, 0, 0),
            )
            num_generated_triples += 1
    return overall_score / num_generated_triples


# start = time.time()
# t = generate_triplets(
#     [
#         ['i like italy and tomorrow i am going there'],
#         ['i like italy.'],
#         ['my favorite book is faust'],
#         ['i like italy so much.'],
#         ['i have already been there last summer with my sister.'],
#         ['we loved their pizza napolitana. what about you?'],
#         ["this is great, me too! i am married and my husband and i have 2 children."],
#         ["my brother likes eating plov."],
#         ["i did not like rain and crowds of tourists."],
#         ["I have been to France and Mont-Saint-Michel is the place I liked the most."],
#         ["hi!"],
#         ["but paris is not in italy."],
#         ["hi! What a sunny day today!"],
#         ["Do you like animals? Yes, and most of all whales."],
#         ["I took a plane and then travelled by car."],
#         ["I have been to France and Mont-Saint-Michel is the place I liked the most."],
#         ["i did not like rain and crowds of tourists."]

#     ])

# print(t)
# print(time.time() - start)


TP, predicted, gold, bleu = 0, 0, 0, 0
bs = 150
sent2triplets = list(sent2triplets.items())[:10]
num_batches = len(sent2triplets) // bs + int(len(sent2triplets) % bs > 0)
for i in range(num_batches):
    curr_input = sent2triplets[i * bs : (i + 1) * bs]
    preds = generate_triplets([[s] for s, _ in curr_input])
    bleu += compute_bleu([triplet for s, triplet in curr_input], preds)
    for (_, gold_triplets), pred in zip(curr_input, preds):
        print(gold_triplets, " ||| ", pred)
        if pred:
            pred_set = set([tuple(t) for t in pred])
            TP += len(set([tuple(t) for t in gold_triplets]).intersection(pred_set))
            predicted += len(pred)
        gold += len(gold_triplets)

precision = TP / predicted * 100
recall = TP / gold * 100
f1 = (2 * precision * recall) / (precision + recall)

print(f"precision: {round(precision, 2)} \nrecall: {round(recall, 2)} \nf1-score: {round(f1, 2)}")
print(f"BLEU: {round(bleu/num_batches*100, 2)}")
