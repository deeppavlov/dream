import argparse
import requests
import json

parser = argparse.ArgumentParser()
parser.add_argument("-pred_f", "--pred_file", type=str, default="tests/test_results.json")
parser.add_argument("-true_f", "--true_file", type=str, default="tests/test_tasks.json")
parser.add_argument("-from_url", "--from_url", type=str, default="http://0.0.0.0:8007/transfertransfo")


def get_response(url, personality, history):
    try:
        data = requests.post(url, json={"personality": [personality], "utterances_histories": [history]})
        return data.json()[0]
    except Exception:
        return ("", 0)


def main():
    args = parser.parse_args()
    cntx = json.load(open(args.true_file, "rt"))
    personality = cntx["personality"]

    valid_flags = []
    res_tasks = []
    for task in cntx["tasks"]:
        responses = []
        for _ in range(task["num_try"]):
            responses.append(get_response(args.from_url, personality, task["utterances_histories"]))
        responses = sorted(responses, key=lambda x: -x[1])
        responses = [
            {
                "valid": not task["targets"] or bool([True for tgt in task["targets"] if tgt in res]),
                "response": res,
                "confidence": conf,
            }
            for res, conf in responses
            if res
        ]
        task["responses"] = responses
        valid = bool([True for res in responses if res["valid"]])
        task["valid"] = valid
        res_tasks.append(task)
        valid_flags.append(not task["targets"] or valid)
    cntx["tasks"] = res_tasks
    json.dump(cntx, open(args.pred_file, "wt", encoding="utf-8"), indent=4)
    for valid in valid_flags:
        assert valid


if __name__ == "__main__":
    main()
