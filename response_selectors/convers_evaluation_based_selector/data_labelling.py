# USAGE example: python response_selectors/convers_evaluation_based_selector/data_labelling.py  \
#                 --dialog_id 5e412fabd655fa53fa6bc9f8 \
#                 --save_dir response_selectors/convers_evaluation_based_selector/labeled_data/
import requests
import json
import argparse
import logging
import glob
import os
import sys

from state_formatters.dp_formatters import cobot_conv_eval_formatter_dialog

sys.path.append(os.getcwd())


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument('--dialog_id', help='dialog id to label')
parser.add_argument('--save_dir', help='directory to save labeled data')
parser.add_argument('--mode', help='add_annotations|label', default='label')

BLACKLIST_URL = "http://localhost:8018/blacklisted_words_batch"
CONV_EVAL_URL = "http://localhost:8004/model"
TOXIC_URL = "http://localhost:8013/model"


def get_dialog_data(dialog_id):
    prod_url = "http://docker-externalloa-lofsuritnple-525614984.us-east-1.elb.amazonaws.com:4242/api/dialogs"
    dialog_url = f"{prod_url}/{dialog_id}"
    return requests.get(dialog_url).json()


def prepare_data(dialog_data):
    utterances = list(dialog_data['utterances'])
    rows = []
    for i in range(len(utterances)):
        if utterances[i]['user']['user_type'] == 'bot':
            if i - 1 < 0:
                user_utts = []
                bot_utts = []
                new_utts = utterances[i:i]
            elif i - 2 < 0:
                user_utts = [{"text": utterances[i - 1]['text']}]
                bot_utts = []
                new_utts = utterances[i - 1:i]
            elif i - 4 < 0:
                user_utts = [{"text": utterances[i - 1]['text']}, {"text": utterances[i - 3]['text']}]
                bot_utt = utterances[i - 2]
                bot_utts = [
                    {'text': bot_utt['text'], 'confidence': bot_utt['confidence'],
                     'skill_name': bot_utt['active_skill']}
                ]
                new_utts = utterances[i - 3:i]
            else:
                bot_utt = utterances[i - 2]
                prev_bot_utt = utterances[i - 4]
                user_utts = [{"text": utterances[i - 1]['text']}, {"text": utterances[i - 3]['text']}]
                bot_utts = [
                    {
                        'text': bot_utt['text'], 'confidence': bot_utt['confidence'],
                        'skill_name': bot_utt['active_skill']},
                    {
                        'text': prev_bot_utt['text'], 'confidence': prev_bot_utt['confidence'],
                        'skill_name': prev_bot_utt['active_skill']}
                ]
                new_utts = utterances[i - 4:i]
            hypots = utterances[i - 1]['hypotheses']

            row = {
                'human_utterances': user_utts,
                'bot_utterances': bot_utts,
                'hypotheses': hypots,
                'utterances': new_utts
            }
            rows.append(row)
    return rows


def label_prepared_data(prepared_data):
    try:
        for row in prepared_data:
            for utt in row["utterances"]:
                print(f'{utt["user"]["user_type"]}: {utt["text"]}')
            assert row['utterances'][-1]['user']['user_type'] == 'human'
            sorted_hypots = list(sorted(
                row['utterances'][-1]["hypotheses"], key=lambda x: x["confidence"], reverse=True)
            )
            for i, h in enumerate(sorted_hypots):
                if h['confidence'] > 0:
                    print(f'{i} hypot: {h["text"]}; skill: {h["skill_name"]}; conf: {h["confidence"]}')
            hypot_nums = input("Type best hypot num(s), separated by comma: ")
            if hypot_nums:
                print(f"You selected: {hypot_nums}")
                for hypot_num in hypot_nums.split(","):
                    hypot_num = int(hypot_num.strip())
                    sorted_hypots[hypot_num]['is_best'] = True
                    row['utterances'][-1]["has_is_best"] = True
            else:
                print("You skipped")
            row['utterances'][-1]['hypotheses'] = sorted_hypots
            print()
    except (Exception, KeyboardInterrupt) as e:
        print(f"EXCEPTION!!!!! {e}. Labeled data saving...")
    return prepared_data


def add_annotations(dialogs):
    new_dialogs = []
    utt_hypots = {}
    for dialog in dialogs:
        hypots = [h["text"] for h in dialog['utterances'][-1]["hypotheses"]]
        blacklist_result = requests.post(BLACKLIST_URL, json={"sentences": hypots}).json()[0]
        toxic_result = requests.post(TOXIC_URL, json={"sentences": hypots}).json()
        toxic_result = [res[0] for res in toxic_result]
        conv_eval_format = cobot_conv_eval_formatter_dialog(dialog)
        conv_eval_result = requests.post(CONV_EVAL_URL, json=conv_eval_format[0]).json()[0]
        logging.debug("***************conv result")
        logging.debug(str(conv_eval_result))

        for i in range(len(blacklist_result["batch"])):
            dialog['hypotheses'][i]['annotations']['blacklisted_words'] = blacklist_result["batch"][i]
            dialog['hypotheses'][i]['annotations']['toxic_classification'] = toxic_result[i]
            dialog['hypotheses'][i]['annotations']['cobot_convers_evaluator_annotator'] = conv_eval_result["batch"][i]
            utt_hypots[dialog['utterances'][-1]['text']] = dialog['hypotheses']

        for utt in dialog["utterances"]:
            if utt['text'] in utt_hypots:
                utt['hypotheses'] = utt_hypots[utt['text']]
        new_dialogs.append(dict(dialog))
    return new_dialogs


def main(dialog_id, labeled_data_dir):
    dialog_data = get_dialog_data(dialog_id)
    prepared_data = prepare_data(dialog_data)
    labeled_data = label_prepared_data(prepared_data)

    with open(f'{labeled_data_dir}/{dialog_id}.json', 'w') as f:
        json.dump(labeled_data, f, ensure_ascii=False, indent=2)


def main_add_annotations(labeled_data_dir):
    for json_file in glob.glob(f"{labeled_data_dir}/*.json", recursive=False):
        print("DEBUG", json_file)
        with open(json_file, 'r') as f:
            dialogs = json.load(f)
        dialogs = add_annotations(dialogs)
        with open(json_file, 'w') as f:
            json.dump(dialogs, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    args = parser.parse_args()
    if args.mode == 'add_annotations':
        main_add_annotations(args.save_dir)
    else:
        main(args.dialog_id, args.save_dir)
