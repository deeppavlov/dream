import argparse
import requests
import json
import traceback
import glob

# import tqdm

parser = argparse.ArgumentParser()
parser.add_argument("-pred_f", "--pred_file", type=str, default="/tmp/test_results.json")
parser.add_argument("-true_f", "--true_file", type=str, default="/global_data/topicalchat_*_tests.json")
parser.add_argument("-from_url", "--from_url", type=str, default="http://0.0.0.0:8034/respond")


def get_response(url, sentences):
    try:
        data = requests.post(url, json={"sentences": sentences, "utterances_histories": [[]] * len(sentences)})
        return data.json()[0]
    except Exception:
        print(traceback.format_exc())
        return ("", 0)


def fuzzy_search_file(file_fuzzy_path):
    if file_fuzzy_path:
        cand_files = glob.glob(file_fuzzy_path)
        return cand_files[-1] if cand_files else None


def main():
    args = parser.parse_args()
    true_file = fuzzy_search_file(args.true_file)
    assert true_file is not None
    cntx = json.load(open(true_file, "rt"))
    # personality = cntx["personality"]

    valid_flags = []
    res_tasks = []
    # for task in tqdm.tqdm(cntx["tasks"]):
    for task in cntx["tasks"]:
        responses = []
        for _ in range(task["num_try"]):
            responses.append(get_response(args.from_url, task["utterances_histories"]))
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
