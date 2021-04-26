from collections import defaultdict
import json


def init_model():
    with open("res_cor.json") as data:
        file = json.load(data)

    dialogues = []
    for d in file[:2]:
        samples = defaultdict(dict)
        result = d["completions"][0]["result"]
        texts_without_labels = d["data"]["text"]
        for sample in result:
            speaker = texts_without_labels[int(sample["value"]["start"])]["speaker"]
            samples[sample["id"]]["speaker"] = speaker
            samples[sample["id"]]["text"] = sample["value"]["text"]
            samples[sample["id"]]["start"] = int(sample["value"]["start"])
            if "paragraphlabels" in sample["value"]:
                samples[sample["id"]]["paragraphlabels"] = sample["value"]["paragraphlabels"][0]
            if "choices" in sample["value"]:
                samples[sample["id"]]["choices"] = sample["value"]["choices"][0]

        sorted_samples = sorted([(samples[sample_id]["start"], sample_id) for sample_id in samples])
        texts = []
        labels = []
        speakers = []
        for _, sample_id in sorted_samples:
            if samples[sample_id]["text"] != "PAUSE":
                texts.append(str(samples[sample_id]["text"]).replace("\n", ""))
                speakers.append(samples[sample_id]["speaker"])
                paragraph_labels = samples[sample_id].get("paragraphlabels", "")
                choices = samples[sample_id].get("choices", "")
                labels.append(paragraph_labels + "." + choices)
        dialogues.append((texts, labels, speakers))

    train_labels = dialogues[1][1]
    test_labels = dialogues[0][1]

    class_dict = {}
    label_to_name = []
    i = 0
    for el in set(train_labels + test_labels):
        class_dict[el] = i
        i = i + 1
        label_to_name.append(el)

    counters = [[0] * len(class_dict) for _ in range(len(class_dict))]

    for label_sequence in (train_labels, test_labels):
        for i, lbl in enumerate(label_sequence):
            if i + 1 < len(label_sequence):
                num_class = class_dict[label_sequence[i]]
                num_class2 = class_dict[label_sequence[i + 1]]
                counters[num_class][num_class2] += 1

    for i in range(len(counters)):
        total_count = sum(counters[i])
        for j in range(len(counters[i])):
            counters[i][j] /= max(total_count, 1)

    return class_dict, counters, label_to_name
