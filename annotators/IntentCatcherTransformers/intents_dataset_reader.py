from collections import OrderedDict
from itertools import chain
from pathlib import Path
from random import shuffle
from typing import Optional

import json
from deeppavlov.core.data.dataset_reader import DatasetReader
from xeger import Xeger


class IntentsJsonReader(DatasetReader):
    """
    Class provides reading intents dataset in .json format:
    ```json
    {
        "intent_phrases": {
            "intent_0": {
                "phrases": [
                    "(alexa ){0,1}(hi|hello)(( there)|( alexa)){0,1}"
                ],
                "reg_phrases": [
                    "hi",
                    "hello"
                ],
                "punctuation": [
                    ".",
                    "!"
                ]
            }
        }
    }
    ```
    to make it compatible with classification models in DeepPavlov pipelines:
    ```json
    [
        ("alexa hi", "intent_0"),
        ...,
    ]
    ```
    """

    @staticmethod
    def generate_phrases(template_re, punctuation, limit=2500):
        x = Xeger(limit=limit)
        phrases = []
        for regex in template_re:
            try:
                phrases += list({x.xeger(regex) for _ in range(limit)})
            except Exception as e:
                print(e)
                print(regex)
                raise e
        phrases = [phrases] + [[phrase + punct for phrase in phrases] for punct in punctuation]
        return list(chain.from_iterable(phrases))

    def read(self, data_path: str, generated_data_path: Optional[str] = None, *args, **kwargs) -> dict:
        """
        Read dataset from `data_path` file with extension `.json`
        Args:
            data_path: file with `.json` extension
        Returns:
            dictionary with data samples.
            Each field of dictionary is a list of tuples (x_i, y_i)
            where `x_i` is a text sample, `y_i` is a class name
        """
        data_types = ["train", "valid", "test"]
        data = {data_type: [] for data_type in data_types}

        for data_type in data_types:
            file_name = kwargs.get(data_type, f"{data_type}.json")
            if file_name is None:
                continue

            file = Path(data_path).joinpath(file_name)
            if file.exists():
                if generated_data_path and Path(generated_data_path).joinpath(file_name).exists():
                    with open(Path(generated_data_path).joinpath(file_name), "r") as fp:
                        data[data_type] = json.load(fp)
                else:
                    with open(file, "r", encoding="utf-8") as fp:
                        all_data = json.load(fp)
                        intent_phrases = OrderedDict(all_data["intent_phrases"])
                        random_phrases = all_data["random_phrases"]
                        # print('Словарь json загружен успешно')
                        random_phrases = self.generate_phrases(random_phrases["phrases"], random_phrases["punctuation"])

                    intent_data = {}
                    for intent, intent_samples in intent_phrases.items():
                        phrases = self.generate_phrases(intent_samples["phrases"], intent_samples["punctuation"])
                        intent_data[intent] = {
                            "generated_phrases": phrases,
                            "num_punctuation": len(intent_samples["punctuation"]),
                        }

                    data[data_type] = [
                        (gen_phrase, [intent])
                        for intent in intent_phrases.keys()
                        for gen_phrase in intent_data[intent]["generated_phrases"]
                    ]
                    data[data_type] += [(gen_phrase, []) for gen_phrase in random_phrases]
                    shuffle(data[data_type])
                    if generated_data_path:
                        Path(generated_data_path).mkdir(exist_ok=True)
                        with open(Path(generated_data_path).joinpath(file_name), "w") as fp:
                            json.dump(data[data_type], fp, indent=2)
            elif data_type == "train":
                raise FileNotFoundError(f"Train file `{file_name}` is not provided in `{data_path}`.")

        return data
