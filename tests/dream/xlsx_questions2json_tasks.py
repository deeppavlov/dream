# %%
import re
import json
import copy
import argparse

import pandas as pd

punct = re.compile(r'[\?\.,\!\'"\)\]]*')

parser = argparse.ArgumentParser()
parser.add_argument(
    "-p",
    "--personality_file_path",
    help="path to json file with personality",
    default="skills/transfertransfo/tests/test_tasks.json",
)
parser.add_argument(
    "-o",
    "--new_tasks_file_path",
    help="path to json file to save converted questions",
    default="skills/transfertransfo/tests/test_question_tasks.json",
)
parser.add_argument(
    "-i",
    "--test_questions_xlsx_path",
    help="path to xlsx file with questions",
    default="tests/dream/test_questions.xlsx",
)
args = parser.parse_args()

template_task = {"utterances_histories": ["hello", "hi"], "num_try": 10, "targets": []}


def create_task(sheet_name, utter, correct_answer=None):
    task = copy.deepcopy(template_task)
    utter = punct.sub("", str(utter).strip().lower())
    task["utterances_histories"].append(utter)
    task["sheet_name"] = sheet_name
    if correct_answer:
        task["correct_answer"] = correct_answer
    return task


dfs = pd.read_excel(args.test_questions_xlsx_path, sheet_name=None, header=None)

tasks = []
for sheet_name, df in dfs.items():
    questions = dfs[sheet_name][0]
    correct_answers = dfs[sheet_name].get(1)
    questions = questions.tolist()
    correct_answers = correct_answers.tolist() if not (correct_answers is None) else [None] * len(questions)
    tasks.extend(
        [
            create_task(sheet_name, question, correct_answer=answer)
            for question, answer in zip(questions, correct_answers)
        ]
    )


json.dump(
    {"personality": json.load(open(args.personality_file_path, "rt"))["personality"], "tasks": tasks},
    open(args.new_tasks_file_path, "wt", encoding="utf-8"),
    indent=4,
)
