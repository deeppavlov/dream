import string

from nltk.tokenize import sent_tokenize, word_tokenize


# Segmentation task
# dataset: one sample = (list of token without punctuations, list of tags):
# [['hi', 'alexa', 'what', 'time', 'is', 'it']]
# [['B-S', ,'O', 'B-Q', 'O', 'O', 'O']]

# Convert cornellmoviequotes dataset to be suitable with the segmentation task


def preprocess(raw_text):
    # input: raw text consisting of sentences without punctuation
    # output: x - list of tokens, y - list of label
    tmp = sent_tokenize(raw_text)

    # remove the long line which consists more than three sentences
    if len(tmp) > 3:
        # print(tmp)
        return [], []

    tmp = [word_tokenize(sent) for sent in tmp]

    x, y = [], []

    for sent in tmp:
        if sent[-1] == "?":
            y.append("B-Q")
        # elif sent[-1].endswith('!'):
        # 	y.append('B-E')
        else:
            y.append("B-S")

        x.extend(sent[:-1])
        y.extend(["O"] * (len(sent) - 2))
    return x, y


def convert_russian_subtitles():
    with open(file="data/russian_subtitles_unique_utterances.txt", mode="r") as f:
        lines = f.readlines()
    X, Y = [], []

    for line in lines:
        tmp = line.strip().lower()
        x, y = preprocess(tmp)
        if x != []:
            X.append(x)
            Y.append(y)

    with open(file="./data/sentseg.txt", mode="w", encoding="utf-8") as fo:
        for x, y in zip(X, Y):
            for word, label in zip(x, y):
                fo.write("{}\t{}\n".format(word, label))
            fo.write("\n")


def convert_cornellmoviequotes():
    with open(file="../datasets/cornellmoviequotes/moviequotes.scripts.txt", mode="r", encoding="latin-1") as f:
        lines = f.readlines()
    X, Y = [], []

    for line in lines:
        tmp = line.split("+++$+++")[-1].strip().lower()
        # print(tmp)

        x, y = preprocess(tmp)

        # print(x)
        # print(y)
        # print('\n')
        if x != []:
            X.append(x)
            Y.append(y)

    with open(file="../datasets/cornqellmoviequotes.txt", mode="w", encoding="utf-8") as fo:
        for x, y in zip(X, Y):
            for word, label in zip(x, y):
                fo.write("{}\t{}\n".format(word, label))
            fo.write("\n")


def convert_dailydialog():
    X, Y = [], []
    with open(file="../datasets/dailydialog.txt", mode="r", encoding="utf-8") as f:
        lines = f.readlines()
    # print(lines[:10])
    # print(len(lines))
    for line in lines:
        tmp = line.strip().lower()
        if len(tmp) == 0:
            continue
        # print(tmp)

        x, y = preprocess(tmp)

        # print(x)
        # print(y)
        # print('\n')
        if x != []:
            X.append(x)
            Y.append(y)

    with open(file="../datasets/dailydialog_sentseg.txt", mode="w", encoding="utf-8") as fo:
        for x, y in zip(X, Y):
            for word, label in zip(x, y):
                fo.write("{}\t{}\n".format(word, label))
            fo.write("\n")


def data_split(x, y, dev_size, test_size):
    from sklearn.model_selection import train_test_split

    X_train, X_test, y_train, y_test = train_test_split(x, y, test_size=test_size, random_state=42)
    X_train, X_dev, y_train, y_dev = train_test_split(
        X_train, y_train, test_size=dev_size / (1 - test_size), random_state=42
    )
    return X_train, y_train, X_dev, y_dev, X_test, y_test


def split_dataset(dataset_name="cornellmoviequotes"):
    X, Y = [], []
    x, y = [], []

    with open(file=f"data/{dataset_name}.txt", mode="r", encoding="utf-8") as f:
        for line in f:
            if line.strip() == "":
                X.append(x)
                Y.append(y)
                x, y = [], []
            else:
                items = line.split()
                x.append(items[0])
                y.append(items[1])

    xtrain, ytrain, xdev, ydev, xtest, ytest = data_split(X, Y, 0.1, 0.1)
    # print(xtrain[:10])
    # print(ytrain[:10])
    # print(len(xtrain), len(ytrain), len(xdev), len(ydev), len(xtest), len(ytest))

    def write2file(sents, labels, filename):
        with open(file=filename, mode="w", encoding="utf-8") as fo:
            for s, l in zip(sents, labels):
                for word, tag in zip(s, l):
                    fo.write("{}\t{}\n".format(word, tag))
                fo.write("\n")

    write2file(xtrain, ytrain, f"data/{dataset_name}_train.txt")
    write2file(xdev, ydev, f"data/{dataset_name}_dev.txt")
    write2file(xtest, ytest, f"data/{dataset_name}_test.txt")


def create_dicts(inp_file, out_file):
    word_counts = {}

    with open(file=inp_file, mode="r", encoding="utf-8") as f:
        for line in f:
            words = line.strip().split()
            if len(words) > 0:
                if words[0] not in word_counts:
                    word_counts[words[0]] = 1
                else:
                    word_counts[words[0]] += 1

    listofTuples = sorted(word_counts.items(), key=lambda x: x[1])

    words = ["<PAD>", "<UNK>"]
    for elem in listofTuples:
        if elem[1] > 3:
            words.append(elem[0])

    word2id = {k: v for (v, k) in enumerate(words)}
    id2word = {k: v for (k, v) in enumerate(words)}

    chars = ["<PAD>", "<UNK>"]
    for word in word2id.keys():
        for c in word:
            if c not in chars:
                chars.append(c)

    char2id = {k: v for (v, k) in enumerate(chars)}
    id2char = {k: v for (k, v) in enumerate(chars)}

    tag2id = {"<PAD>": 0, "B-S": 1, "B-Q": 2, "O": 3}
    id2tag = {0: "<PAD>", 1: "B-S", 2: "B-Q", 3: "O"}

    print(word2id)
    print(char2id)
    print(len(word2id), len(id2word), len(char2id), len(id2char))

    import pickle

    with open(out_file, "wb") as f:
        pickle.dump(
            {
                "word2id": word2id,
                "id2word": id2word,
                "char2id": char2id,
                "id2char": id2char,
                "tag2id": tag2id,
                "id2tag": id2tag,
            },
            f,
        )


def data_statistic(file):
    stat = {"samples": 0, "total_words": 0, "B-S": 0, "B-Q": 0, "O": 0}
    with open(file=file, mode="r") as f:
        for line in f:
            if len(line.strip()) > 0:
                word, tag = line.strip().split("\t")
                stat[tag] += 1
                stat["total_words"] += 1
            else:
                stat["samples"] += 1

    print(stat)


def create_dailydialog_for_deeppavlov():
    with open(
        file="../datasets/ijcnlp_dailydialog/dailydialog_for_deeppavlov/dailydialog_deeppavlov2.txt",
        mode="w",
        encoding="utf-8",
    ) as fo:
        for dialog in open(
            file="../datasets/ijcnlp_dailydialog/dialogues_text.txt", mode="r", encoding="utf-8"
        ).readlines():
            utterances = dialog.lower().replace("! ?", "!").replace("? !", "?").replace("!", ".").split("__eou__")[:-1]
            for utt in utterances:
                if len(utt) > 200:
                    continue
                x, y = "", ""
                s = word_tokenize(utt)
                for word in s:
                    if word in [".", "?", "!"]:
                        y += word + " "
                    elif word not in string.punctuation:
                        x += word + " "
                        y += word + " "
                if y[-2] in [".", "?", "!"]:
                    fo.write("{} [SEP] {}\n".format(x[:-1], y[:-1]))

            # if len(y) == 0:
            # 	continue
            # y = y.replace("!", ".").replace(",", "").replace(" ’ ", "'").replace("  ", " ").strip()
            # if y[-1] not in [".", "?"]:
            # 	print(y)
            # x = y.replace("?", "").replace(".", "").replace("!", "").replace("  ", " ").strip()
            # if len(x.strip()) > 0:
            # 	fo.write("{} [SEP] {}\n".format(x, y))


def split_dailydialog_for_deeppavlov():
    with open(
        file="../datasets/ijcnlp_dailydialog/dailydialog_for_deeppavlov/dailydialog_deeppavlov2.txt",
        mode="r",
        encoding="utf-8",
    ) as f:
        samples = f.readlines()
    n = len(samples)
    train = samples[: (int)(n * 0.8)]
    val = samples[len(train) : (int)(n * 0.9)]
    test = samples[len(train) + len(val) :]
    print(len(samples), len(train), len(val), len(test))

    with open(
        file="../datasets/ijcnlp_dailydialog/dailydialog_for_deeppavlov/train2.txt", mode="w", encoding="utf-8"
    ) as fo:
        fo.writelines(train)
    with open(
        file="../datasets/ijcnlp_dailydialog/dailydialog_for_deeppavlov/valid2.txt", mode="w", encoding="utf-8"
    ) as fo:
        fo.writelines(val)
    with open(
        file="../datasets/ijcnlp_dailydialog/dailydialog_for_deeppavlov/test2.txt", mode="w", encoding="utf-8"
    ) as fo:
        fo.writelines(test)


# convert = {"Q": "?", "S": ".", "": ""}
# def SentSegRestoreSent(x, y):
#     assert len(x) == len(y)
#     if len(y) == 0:
#         return ""
#     sent = x[0]
#     punct = "" if y[0] == "O" else convert[y[0][-1]]
#     for word, tag in zip(x[1:], y[1:]):
#         if tag != "O":
#             sent += punct
#             punct = convert[tag[-1]]
#         sent += " " + word
#     sent += punct

#     return sent

# with open(file="/home/theanh/.deeppavlov/downloads/sentseg_dailydialog/train.txt", mode="w", encoding="utf-8") as fo:
# 	x, y = [], []
# 	for line in open(file="models/dailydialog_811/train.txt", mode="r", encoding="utf-8").readlines():
# 		items = line.strip().split()
# 		if len(items) == 0:
# 			if len(x) > 0:
# 				xs = " ".join(x)
# 				ys = SentSegRestoreSent(x, y)
# 				fo.write(f"{xs} [SEP] {ys}\n")
# 				x, y = [], []
# 		else:
# 			x.append(items[0].strip())
# 			y.append(items[1].strip())


# import pickle
# print(pickle.load(open("models/dailydialog_811/params.pkl", "rb")))

#
# with open(file="/home/theanh/.deeppavlov/downloads/sentseg_dailydialog/test.txt", mode="w", encoding="utf-8") as fo:
# 	for line in open(file="models/dailydialog_811/test.txt", mode="r", encoding="utf-8").readlines():
# 		if len(line.strip()) > 0:
# 			line = line.replace("B-Q", "B-?").replace("B-S", "B-.")
# 		fo.write(line)

convert_russian_subtitles()

split_dataset(dataset_name="ru_sentseg")

create_dicts("data/ru_sentseg.txt", "data/ru_sentseg_dict.pkl")

# data_statistic("models/dailydialog/train.txt")
# data_statistic("models/dailydialog/dev.txt")
# data_statistic("models/dailydialog/test.txt")

# data_statistic("models/cornellmovie_811/train.txt")
# data_statistic("models/cornellmovie_811/dev.txt")
# data_statistic("models/cornellmovie_811/test.txt")

# create_dailydialog_for_deeppavlov()

# split_dailydialog_for_deeppavlov()
