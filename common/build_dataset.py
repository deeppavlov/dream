import os
import nltk.data

def build_dataset(dataset_path, original_file_path):
    if not os.path.exists(dataset_path):
        os.mkdir(dataset_path)
    tokenizer = nltk.data.load("tokenizers/punkt/english.pickle")
    with open(original_file_path, "r") as f:
        i = 0
        buf = ""
        data = f.read()
        data = tokenizer.tokenize(data)

        for item in data:
            buf += item
            words = buf.split(" ")
            if len(words) > 100:
                i += 1
                new_f = dataset_path + str(i) + ".txt"
                with open(new_f, "w") as f_out:
                    f_out.write(buf)
                buf = ""