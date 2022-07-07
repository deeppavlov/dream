# USAGE example: python response_selectors/convers_evaluation_based_selector/measure_quality.py  \
#                        --data_dir response_selectors/convers_evaluation_based_selector/labeled_data/
# example with url: python response_selectors/convers_evaluation_based_selector/measure_quality.py \
#                   --data_dir response_selectors/convers_evaluation_based_selector/labeled_data/  \
#                   --url http://192.168.10.54:8009/respond
import argparse
import logging
import glob
import json
import requests


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument("--data_dir", help="directory with labeled data")
parser.add_argument(
    "--url",
    help="Conversation evaluator url. None by default, so "
    "it calcs accurcay using active_skill in utterances from json",
    default=None,
)


def measure_quality_by_checking_file(labeled_data_json, url=None):
    with open(labeled_data_json, "r") as f:
        labeled_data = json.load(f)

    goods = 0
    total = 0
    for row in labeled_data:
        for i, utt in enumerate(row["utterances"]):
            if utt["user"]["user_type"] == "bot" and i > 0:
                prev_utt = row["utterances"][i - 1]
                if not prev_utt.get("has_is_best"):
                    continue

                if url:
                    sub_row = dict(row)
                    sub_row["utterances"] = sub_row["utterances"][0:i]
                    # Reverse because data_labelling.py saves it in reverse format
                    sub_row["human_utterances"] = sub_row["human_utterances"][::-1][0:i]
                    sub_row["bot_utterances"] = sub_row["bot_utterances"][::-1][0 : i - 1]
                    sub_row["human"] = {"profile": {}}
                    json_data = {"dialogs": [sub_row]}
                    result = requests.post(url, json=json_data).json()
                    utt = {"active_skill": result[0][0], "text": result[0][1]}
                for hypot in prev_utt["hypotheses"]:
                    eql_skill_and_text = utt["active_skill"] == hypot["skill_name"] and utt["text"] == hypot["text"]
                    if eql_skill_and_text and hypot.get("is_best") is True:
                        goods += 1
                        break
                total += 1
    if total == 0:
        total = 1
    return {"quality": goods / total, "goods": goods, "total": total}


def main(labeled_data_dir, url):
    qualities = []
    for labeled_data_json in glob.glob(f"{labeled_data_dir}/*.json"):
        quality = measure_quality_by_checking_file(labeled_data_json, url)
        qualities.append(quality)

    goods = 0
    total = 0
    for quality_dict in qualities:
        goods += quality_dict["goods"]
        total += quality_dict["total"]
    acc = goods / total
    print(f"Overall accuracy: {acc}")
    assert acc >= 0.51, print("Accuracy less then prev best 0.51")


if __name__ == "__main__":
    args = parser.parse_args()
    main(args.data_dir, args.url)
