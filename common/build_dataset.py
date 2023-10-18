import os
from pathlib import Path
from typing import List, Dict


def build_dataset(dataset_path: str, doc_paths: List[str]) -> Dict[str, List[str]]:
    """Builds dataset with small chunks of files (<100 words) in given dataset_path.

    Args:
        dataset_path: Path to folder where the dataset is created.
        doc_paths: A list of paths to files to be included in the dataset.

    Returns:
        A dict mapping initial paths to files with a list of paths to their chunks.
    """
    dataset_path = Path(dataset_path)
    if not os.path.exists(dataset_path):
        os.mkdir(dataset_path)
    i = 1
    docs_to_parts_dict = {}
    for filepath in doc_paths:
        with open(filepath, "r") as f:
            list_files = []
            buf = ""
            data = f.read()
            data = data.split("\n")

            for item in data:
                buf_test = buf + f" {item}"
                words = buf_test.strip().split(" ")
                if len(words) > 150:
                    new_filepath = dataset_path / f"{i}.txt"
                    i += 1
                    with open(new_filepath, "w") as f_out:
                        f_out.write(buf)
                    buf = item
                    list_files.append(new_filepath)
                else:
                    buf = buf_test
            if buf:
                new_filepath = dataset_path / f"{i}.txt"
                with open(new_filepath, "w") as f_out:
                    f_out.write(buf)
                list_files.append(new_filepath)
        docs_to_parts_dict[filepath] = list_files  # todo: think about keys
    return docs_to_parts_dict


def get_text_for_candidates(dataset_path: str, raw_candidates: List[str]) -> str:
    """Gets texts of candidates from each filename in raw_candidates.

    Args:
        dataset_path: Path to folder where the dataset is stored.
        raw_candidates: A list of names of candidate files to extract text from.

    Returns:
        A string containing texts of all candidate files. Each file text is preceded by its number:

        '1. Candidate text n1. 2. Candidate text n2. 3. Candidate text n3.'
    """
    num_candidates = []
    nums = 0
    for f_name in raw_candidates:
        nums += 1
        with open(dataset_path + f_name) as f:
            num_candidates.append(f"{nums}. {f.read()}")
    return " ".join(num_candidates)
