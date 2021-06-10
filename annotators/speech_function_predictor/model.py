from collections import defaultdict
import json
import re


def cut_labels(list_of_labels):
    for i in range(len(list_of_labels)):
        if 'Support.' in list_of_labels[i]:
            if 'Register' not in list_of_labels[i] and 'Engage' not in list_of_labels[i]:
                list_of_labels[i] = re.sub('Support.', '', list_of_labels[i])
        if 'Confront.' in list_of_labels[i]:
            list_of_labels[i] = re.sub('Confront.', '', list_of_labels[i])
        if 'Append' in list_of_labels[i]:
            list_of_labels[i] = re.sub('Append', 'Prolong', list_of_labels[i])
        if 'Initiate.' in list_of_labels[i]:
            list_of_labels[i] = re.sub('Initiate.', '', list_of_labels[i])
        if 'Challenge.' in list_of_labels[i]:
            list_of_labels[i] = re.sub('Challenge.', '', list_of_labels[i])
        if 'Answer' in list_of_labels[i]:
            list_of_labels[i] = 'React.Rejoinder.Response.Resolve'
        if 'Open.Opinion' in list_of_labels[i]:
            list_of_labels[i] = re.sub('Open.Opinion', 'Opinion', list_of_labels[i])
        if 'Open.Fact' in list_of_labels[i]:
            list_of_labels[i] = re.sub('Open.Fact', 'Fact', list_of_labels[i])
        if 'Open.Fact' in list_of_labels[i]:
            list_of_labels[i] = re.sub('Open.Fact', 'Fact', list_of_labels[i])
        if 'Decline' in list_of_labels[i]:
            list_of_labels[i] = re.sub('Decline', 'Contradict', list_of_labels[i])
        if 'Accept' in list_of_labels[i]:
            list_of_labels[i] = re.sub('Accept', 'Affirm', list_of_labels[i])
        if 'Response.Re-challenge' in list_of_labels[i]:
            list_of_labels[i] = re.sub('Response.Re-challenge', 'Re-challenge', list_of_labels[i])
        if 'Response.Refute' in list_of_labels[i]:
            list_of_labels[i] = re.sub('Response.Refute', 'Counter', list_of_labels[i])
        if 'Response.Acquiesce' in list_of_labels[i]:
            list_of_labels[i] = re.sub('Response.Acquiesce', 'Response.Resolve', list_of_labels[i])
        if 'Detach' in list_of_labels[i]:
            list_of_labels[i] = 'React.Rejoinder.Rebound'
        if 'Rejoinder.Develop.Elaborate' in list_of_labels[i]:
            list_of_labels[i] = re.sub('Rejoinder', 'Respond', list_of_labels[i])
        if 'React.Respond.Disengage' in list_of_labels[i]:
            list_of_labels[i] = 'React.Respond.Support.Register'
        if 'Response.Repair' in list_of_labels[i]:
            list_of_labels[i] = 'React.Respond.Develop.Extend'
        if 'React.Rejoinder.Counter' in list_of_labels[i]:
            list_of_labels[i] = 'Rejoinder.Counter'
        if 'Closed.Fact' in list_of_labels[i]:
            list_of_labels[i] = re.sub('Closed.Fact', 'Fact', list_of_labels[i])
        if 'Closed.Opinion' in list_of_labels[i]:
            list_of_labels[i] = re.sub('Closed.Opinion', 'Opinion', list_of_labels[i])
        if 'React.Rejoinder.Response.Resolve' in list_of_labels[i]:
            list_of_labels[i] = re.sub('Closed.Opinion', 'Opinion', list_of_labels[i])
    return list_of_labels


def init_model():
    with open('common/speech_functions/res_cor.json') as data:
        file = json.load(data)

    dialogues = []
    for d in file[:2]:
        samples = defaultdict(dict)
        result = d['completions'][0]['result']
        texts_without_labels = d['data']['text']
        for sample in result:
            speaker = texts_without_labels[int(sample['value']['start'])]['speaker']
            samples[sample['id']]['speaker'] = speaker
            samples[sample['id']]['text'] = sample['value']['text']
            samples[sample['id']]['start'] = int(sample['value']['start'])
            if 'paragraphlabels' in sample['value']:
                samples[sample['id']]['paragraphlabels'] = sample['value']['paragraphlabels'][0]
            if 'choices' in sample['value']:
                samples[sample['id']]['choices'] = sample['value']['choices'][0]

        sorted_samples = sorted([(samples[sample_id]['start'], sample_id) for sample_id in samples])
        texts = []
        labels = []
        speakers = []
        for _, sample_id in sorted_samples:
            if samples[sample_id]['text'] != 'PAUSE':
                texts.append(str(samples[sample_id]['text']).replace('\n', ''))
                speakers.append(samples[sample_id]['speaker'])
                paragraph_labels = samples[sample_id].get('paragraphlabels', '')
                choices = samples[sample_id].get('choices', '')
                labels.append(paragraph_labels + '.' + choices)
        dialogues.append((texts, labels, speakers))

    train_labels = dialogues[1][1]
    test_labels = dialogues[0][1]

    class_dict = {}
    label_to_name = []
    i = 0
    for el in set(cut_labels(train_labels) + cut_labels(test_labels)):
        class_dict[el] = i
        i = i + 1
        label_to_name.append(el)

    A = [[0] * len(class_dict) for _ in range(len(class_dict))]

    for label_sequence in (train_labels, test_labels):
        for i, lbl in enumerate(label_sequence):
            if i + 1 < len(label_sequence):
                num_class = class_dict[label_sequence[i]]
                num_class2 = class_dict[label_sequence[i + 1]]
                A[num_class][num_class2] += 1

    for i in range(len(A)):
        total_count = sum(A[i])
        for j in range(len(A[i])):
            A[i][j] /= max(total_count, 1)
    return class_dict, label_to_name, A
