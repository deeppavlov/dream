import pandas as pd
import json

mappintg_f = open("ekman_mapping.json")
emotions_mapping = json.load(mappintg_f)

with open("emotions.txt") as f:
    emotions = f.readlines()

emotions = [x.replace("\n", "") for x in emotions]

orig2compressed = {}

for key, value in emotions_mapping.items():
    for emotion in value:
        orig_index = emotions.index(emotion)
        # orig2compressed[orig_index] = emotions.index(key)
        orig2compressed[str(orig_index)] = key

orig2compressed["27"] = "neutral"

columns = ["text", "emotion", "name"]

dev_df = pd.read_csv("dev.tsv", sep="\t", names=columns)
test_df = pd.read_csv("test.tsv", sep="\t", names=columns)
train_df = pd.read_csv("train.tsv", sep="\t", names=columns)


def compress_labels_in_df(df):
    emotions_column = list(df.emotion)
    # emotions_column = [orig2compressed[int(x.split(",")[0])] for x in emotions_column]
    # emotions_column = [",".join(orig2compressed[y] for y in x.split(",")]) for x in emotions_column]
    emotions_column = [orig2compressed[x.split(",")[0]] for x in emotions_column]
    new_df = pd.DataFrame()
    new_df["text"] = list(df.text)
    new_df["emotion"] = emotions_column
    return new_df


new_dev = compress_labels_in_df(dev_df)
new_dev.to_csv("dev.csv")

new_test = compress_labels_in_df(test_df)
new_test.to_csv("test.csv")

new_train = compress_labels_in_df(train_df)
new_train.to_csv("train.csv")
