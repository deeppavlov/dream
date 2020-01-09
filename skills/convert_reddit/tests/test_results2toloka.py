import argparse
import json

parser = argparse.ArgumentParser()
parser.add_argument("--json_infile", type=str, default="test_question_tasks_results.json", help="from tasks json file")
parser.add_argument("--json_outfile", type=str, default="toloka_test_question_tasks_results.json", help="output file")


def main():
    args = parser.parse_args()
    cntx = json.load(open(args.json_infile, "rt"))
    tasks = []
    for task in cntx["tasks"]:
        responses = {
            resp.get("response", ""): resp
            for resp in task["responses"]
            if resp.get("response") and resp.get("response") != "sorry"
        }
        responses = sorted(responses.values(), key=lambda x: -x.get("confidence", 0))
        task["responses"] = responses
        tasks.append(task)

    json.dump(cntx, open(args.json_outfile, "wt", encoding="utf-8"), indent=4)


if __name__ == "__main__":
    main()
