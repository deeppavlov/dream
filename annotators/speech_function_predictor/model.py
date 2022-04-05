# from collections import defaultdict
# import re
# import json


# def cut_labels(list_of_labels):
#     for i in range(len(list_of_labels)):
#         if list_of_labels[i][-1] == ".":
#             list_of_labels[i] = list_of_labels[i].strip(".")
#         if "Append" in list_of_labels[i]:
#             list_of_labels[i] = re.sub("Append", "Prolong", list_of_labels[i])
#         if "Initiate." in list_of_labels[i]:
#             list_of_labels[i] = re.sub("Initiate.", "", list_of_labels[i])
#         if "Answer" in list_of_labels[i]:
#             list_of_labels[i] = "React.Rejoinder.Support.Response.Resolve"
#         if "Open.Opinion" in list_of_labels[i]:
#             list_of_labels[i] = re.sub("Open.Opinion", "Opinion", list_of_labels[i])
#         if "Re-challenge" in list_of_labels[i]:
#             list_of_labels[i] = "React.Rejoinder.Confront.Response.Re-challenge"
#         if "Open.Fact" in list_of_labels[i]:
#             list_of_labels[i] = re.sub("Open.Fact", "Fact", list_of_labels[i])
#         if "Open.Fact" in list_of_labels[i]:
#             list_of_labels[i] = re.sub("Open.Fact", "Fact", list_of_labels[i])
#         if "Decline" in list_of_labels[i]:
#             list_of_labels[i] = re.sub("Decline", "Contradict", list_of_labels[i])
#         if "Accept" in list_of_labels[i]:
#             list_of_labels[i] = re.sub("Accept", "Affirm", list_of_labels[i])
#         if "Response.Refute" in list_of_labels[i]:
#             list_of_labels[i] = re.sub("Response.Refute", "Counter", list_of_labels[i])
#         if "Response.Acquiesce" in list_of_labels[i]:
#             list_of_labels[i] = re.sub("Response.Acquiesce", "Response.Resolve", list_of_labels[i])
#         if "Detach" in list_of_labels[i]:
#             list_of_labels[i] = "React.Rejoinder.Rebound"
#         if "Rejoinder.Develop.Elaborate" in list_of_labels[i]:
#             list_of_labels[i] = re.sub("Rejoinder", "Respond", list_of_labels[i])
#         if "React.Respond.Disengage" in list_of_labels[i]:
#             list_of_labels[i] = "React.Respond.Support.Register"
#         if "Response.Repair" in list_of_labels[i]:
#             list_of_labels[i] = "React.Respond.Support.Develop.Extend"
#         if "Counter" in list_of_labels[i]:
#             list_of_labels[i] = "React.Rejoinder.Confront.Challenge.Counter"
#         if "Closed.Fact" in list_of_labels[i]:
#             list_of_labels[i] = re.sub("Closed.Fact", "Fact", list_of_labels[i])
#         if "Closed.Opinion" in list_of_labels[i]:
#             list_of_labels[i] = re.sub("Closed.Opinion", "Opinion", list_of_labels[i])
#         if "React.Rejoinder.Response.Resolve" in list_of_labels[i]:
#             list_of_labels[i] = re.sub("Closed.Opinion", "Opinion", list_of_labels[i])
#         if "Sustain.Continue.Develop.Elaborate" in list_of_labels[i]:
#             list_of_labels[i] = "Sustain.Continue.Prolong.Elaborate"
#         if "Rebound" in list_of_labels[i]:
#             list_of_labels[i] = "React.Rejoinder.Support.Challenge.Rebound"
#         if "React.Rejoinder.Confront.Develop.Elaborate" in list_of_labels[i]:
#             list_of_labels[i] = "React.Rejoinder.Support.Develop.Elaborate"
#         if "Fact.Extend" in list_of_labels[i]:
#             list_of_labels[i] = "Open.Give.Fact"
#     return list_of_labels


# def init_model():
#     with open("res_cor.json") as data:
#         file = json.load(data)

#     dialogues = []
#     for d in file[:2]:
#         samples = defaultdict(dict)
#         result = d["completions"][0]["result"]
#         texts_without_labels = d["data"]["text"]
#         for sample in result:
#             speaker = texts_without_labels[int(sample["value"]["start"])]["speaker"]
#             samples[sample["id"]]["speaker"] = speaker
#             samples[sample["id"]]["text"] = sample["value"]["text"]
#             samples[sample["id"]]["start"] = int(sample["value"]["start"])
#             if "paragraphlabels" in sample["value"]:
#                 samples[sample["id"]]["paragraphlabels"] = sample["value"]["paragraphlabels"][0]
#             if "choices" in sample["value"]:
#                 samples[sample["id"]]["choices"] = sample["value"]["choices"][0]

#         sorted_samples = sorted([(samples[sample_id]["start"], sample_id) for sample_id in samples])
#         texts = []
#         labels = []
#         speakers = []
#         for _, sample_id in sorted_samples:
#             if samples[sample_id]["text"] != "PAUSE":
#                 texts.append(str(samples[sample_id]["text"]).replace("\n", ""))
#                 speakers.append(samples[sample_id]["speaker"])
#                 paragraph_labels = samples[sample_id].get("paragraphlabels", "")
#                 choices = samples[sample_id].get("choices", "")
#                 labels.append(paragraph_labels + "." + choices)
#         dialogues.append((texts, labels, speakers))

#     train_labels = dialogues[1][1]
#     test_labels = dialogues[0][1]

#     class_dict = {}
#     label_to_name = []
#     i = 0
#     for el in set(cut_labels(train_labels) + cut_labels(test_labels)):
#         class_dict[el] = i
#         i = i + 1
#         label_to_name.append(el)

#     print("Class Dict:", class_dict)
#     counters = [[0] * len(class_dict) for _ in range(len(class_dict))]

#     for label_sequence in (train_labels, test_labels):
#         for i, lbl in enumerate(label_sequence):
#             if i + 1 < len(label_sequence):
#                 num_class = class_dict[label_sequence[i]]
#                 num_class2 = class_dict[label_sequence[i + 1]]
#                 counters[num_class][num_class2] += 1

#     for i in range(len(counters)):
#         total_count = sum(counters[i])
#         for j in range(len(counters[i])):
#             counters[i][j] /= max(total_count, 1)

#     return class_dict, counters, label_to_name


# -*- coding: utf-8 -*-
"""Untitled8.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/16KZA7WP9XwwGL_c55ueOMpVpKrYiNBUM
"""

from collections import defaultdict

def init_model():
    with open("labels.txt") as data:
        labels = data.read()
    
    labels = labels.replace('\n','')
    labels = labels.split(',')

    class_dict = {}
    label_to_name = []
    i = 0
    for el in set(labels):
        class_dict[el] = i
        i = i + 1
        label_to_name.append(el)

    print("Class Dict:", class_dict)
    counters = [[0] * len(class_dict) for _ in range(len(class_dict))]

    for label_sequence in (labels):
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


    def run_test():
        model_test_data = ["Reply.Acknowledge"]
        model_hypothesis = requests.post(MODEL_URL, json=model_test_data).json()

        print("test name: sfp model_hypothesis")
        assert model_hypothesis == [{}]

        annotation_test_data = ["Reply.Acknowledge"]
        annotation_hypothesis = requests.post(ANNOTATION_URL, json=annotation_test_data).json()

        print("test name: sfp annotation_hypothesis")
        assert annotation_hypothesis == [{"batch": [{}]}]

        print("Success")


if __name__ == "__main__":
    run_test()
