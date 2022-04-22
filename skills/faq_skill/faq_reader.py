from pathlib import Path

import pandas as pd
from deeppavlov.core.data.dataset_reader import DatasetReader


class FAQJsonReader(DatasetReader):
    """
    Class provides reading FAQ dataset in .json format:
    ```json
    [
        {
            "examples": ["hi", "hello"],
            "responses": ["Hi! This is a Dream Socialbot!"]
        },
        {
            "examples": ["how are you", "how are you doing"],
            "responses": ["I'm great!", "I'm good. How are you?"]
        }
    ]
    ```
    to make it compatible with classification models in DeepPavlov pipelines:
    ```json
    [
        ("hi", "response_0"),
        ...,
        ("how are you doing", "response_1")
    ]
    ```
    and responses_map contains mapping (for further usage in a pipeline to generate a response:
    ```json
    {
        "response_0": ["Hi! This is a Dream Socialbot!"],
        "response_1": ["I'm great!", "I'm good. How are you?"]
    }
    ```
    """
    responses_map = {}

    def read(self, data_path: str, *args, **kwargs) -> dict:
        """
        Read dataset from data_path directory.
        Reading files are all data_types + extension (.json)
        (i.e for data_types=["train", "valid"] files "train.json" and "valid.json" from data_path will be read)
        Args:
            data_path: directory with files
        Returns:
            dictionary with types from data_types.
            Each field of dictionary is a list of tuples (x_i, y_i)
        """
        data_types = ["train", "valid", "test"]
        data = {data_type: [] for data_type in data_types}

        for data_type in data_types:
            file_name = kwargs.get(data_type, f"{data_type}.json")
            if file_name is None:
                continue

            file = Path(data_path).joinpath(file_name)
            if file.exists():
                df = pd.read_json(file)
                x = kwargs.get("x", "examples")
                y = kwargs.get('y', 'responses')
                # row[x] is a list of strings (samples of requests)
                # row[y] is a list of strings (possible responses for random choice)
                self.responses_map = {f"response_{i}": row[y] for i, row in df.iterrows()}
                data[data_type] = [(sample, f"response_{i}") for i, row in df.iterrows() for sample in row[x]]
            elif data_type == "train":
                raise FileNotFoundError(f"Train file `{file_name}` is not provided in `{data_path}`.")

        return data
