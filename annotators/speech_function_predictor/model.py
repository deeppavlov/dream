import json

def init_model():

    with open('sf_pairs.json', 'r') as json_file:
        lines = json_file.readlines()

    prev_sfs = [json.loads(line)['prev_sf'] for line in lines]
    current_sfs = [json.loads(line)['current_sf'] for line in lines]

    class_dict = {}
    label_to_name = []
    i = 0
    for el in set(prev_sfs + current_sfs):
        class_dict[el] = i
        i = i + 1
        label_to_name.append(el)

    print("Class Dict:", class_dict)
    counters = [[0] * len(class_dict) for _ in range(len(class_dict))]

    for idx in zip(prev_sfs, current_sfs):
        num_class1 = class_dict[idx[0]]
        num_class2 = class_dict[idx[1]]
        counters[num_class1][num_class2] += 1
    for i in range(len(counters)):
        total_count = sum(counters[i])
        for j in range(len(counters[i])):
            counters[i][j] /= max(total_count, 1)
            counters[i][j] = round(counters[i][j], 2)

    return class_dict, counters, label_to_name
