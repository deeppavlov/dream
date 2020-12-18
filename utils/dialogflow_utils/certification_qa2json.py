# %%
import json
import argparse
import collections

import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument(
    "-o",
    "--output_json_file_path",
    help="path to json file to save converted questions",
    default="/tmp/test_question.json",
)
parser.add_argument(
    "-i",
    "--input_certification_qa_xlsx_path",
    help="path to xlsx file with questions",
    default="tests/dream/test_questions.xlsx",
)
args = parser.parse_args()


dfs = pd.read_excel(args.input_certification_qa_xlsx_path, sheet_name=None, header=None, engine="openpyxl")

tasks = collections.defaultdict(list)
for sheet_name, df in dfs.items():
    questions = dfs[sheet_name][0]
    questions = questions.tolist()
    tasks[sheet_name] += questions


json.dump(
    tasks,
    open(args.output_json_file_path, "wt", encoding="utf-8"),
    indent=4,
)
