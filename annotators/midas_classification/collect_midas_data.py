import pandas as pd

data_type = "train"

with open(f"da_data/{data_type}.txt", "r") as f:
    data = f.read().splitlines()

print(len(data))

df = {"text": [],
      # "labels": [],
      "joint_labels": []
      }
for row in data:
    splitted_row = row.split(" ## ")
    try:
        splitted_row[1] = splitted_row[1].split(";")
        splitted_row[1] = [el for el in splitted_row[1] if el]
        df["text"].append(splitted_row[0])
        # df["labels"].append(splitted_row[1])
        df["joint_labels"].append(";".join(splitted_row[1]))
    except Exception:
        pass

data = pd.DataFrame(df)
print(data.shape)
print(data.head())
print(data["joint_labels"].value_counts())

data.to_csv(f"midas_{data_type}.csv", index=False, sep=",")

considered = ["neg_answer", "open_question_factual", "open_question_opinion",
              "opinion", "other_answers", "pos_answer", "statement", "yes_no_question"]
questions = ["open_question_factual", "open_question_opinion",
             "yes_no_question"]

with open(f"da_data/{data_type}.txt", "r") as f:
    data = f.read().splitlines()

print(len(data))

df = {"text": [],
      "binary_labels": [],
      "joint_labels": []
      }
for row in data:
    splitted_row = row.split(" ## ")
    try:
        splitted_row[1] = splitted_row[1].split(";")
        splitted_row[1] = [el for el in splitted_row[1] if el and el in considered]
        if len(splitted_row[1]) == 1:
            df["text"].append(splitted_row[0])
            df["joint_labels"].append(splitted_row[1][0])
            if splitted_row[1][0] in questions:
                df["binary_labels"].append("some_question")
            else:
                df["binary_labels"].append("some_statement")

    except Exception:
        pass

data = pd.DataFrame(df)
print(data.shape)
print(data.head())
print(data["joint_labels"].value_counts())
print(data["binary_labels"].value_counts())
data.to_csv(f"~/.deeppavlov/downloads/midas/midas_part_classes_{data_type}.csv", index=False, sep=",")
