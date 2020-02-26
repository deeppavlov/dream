import argparse
import csv
import statistics

parser = argparse.ArgumentParser()
parser.add_argument('-pred_f', '--pred_file', type=str)
parser.add_argument('-true_f', '--true_file', type=str)
parser.add_argument('-time_limit', '--time_limit', type=float, default=3)


def main():
    args = parser.parse_args()

    with open(args.pred_file, 'r', newline='') as f:
        reader = csv.reader(f, delimiter=' ')
        pred_data = [row for row in reader][1:]
        active_skills = [row[1] for row in pred_data]
        pred_data = [row[-4:] for row in pred_data]

    with open(args.true_file, 'r', newline='') as f:
        reader = csv.reader(f, delimiter=' ')
        true_data = [row for row in reader][1:]
    proc_times = [float(r[0]) for r in pred_data]
    mean_proc_time = statistics.mean(proc_times)

    print(f'Mean proc time: {mean_proc_time}')
    assert statistics.mean(proc_times) <= args.time_limit, print(
        f'Mean proc time: {mean_proc_time} > {args.time_limit}')
    for pred_r, true_r, skill in zip(pred_data, true_data, active_skills):
        true_sents = set([sent.lower().replace('\n', ' ').replace('  ', ' ') for sent in true_r[2:]])
        acceptable_skill_names = true_r[0]
        assert skill != "exception", print("ERROR: exception in gold phrases".format(pred_r[-1], true_sents))

        passed_acceptable_skills = True
        passed_gold_phrases = True

        if acceptable_skill_names.strip():
            if acceptable_skill_names[0] == "!":
                # отрицание возможно только для одного скилла!!!
                skill_name = acceptable_skill_names[1:]
                if skill != skill_name:
                    passed_acceptable_skills = False
                    print(f"FOUND POSSIBLE ERROR: pred skill: {skill} is PROHIBITED: {skill_name}")
            else:
                acceptable_skill_names = acceptable_skill_names.split(";")
                if skill not in acceptable_skill_names:
                    passed_acceptable_skills = False
                    print(f"FOUND POSSIBLE ERROR: pred skill: {skill} "
                          f"NOT IN Acceptable skill names: {acceptable_skill_names}")

        if true_sents:
            checked = False
            for true_sent in true_sents:
                if true_sent in pred_r[-1].lower().replace('\n', ' ').replace('  ', ' '):
                    checked = True
            if not checked:
                passed_gold_phrases = False
                print("FOUND POSSIBLE ERROR: {} not in {}".format(pred_r[-1], true_sents))

        print(f"Acceptable skill names: `{acceptable_skill_names}`.\n"
              f"Passed acceptable skill names: `{passed_acceptable_skills}`.\n"
              f"True sentences: `{true_sents}`.\n"
              f"Passed true sentences: `{passed_gold_phrases}`.")

        if len(acceptable_skill_names) > 0 or len(true_sents) > 0:
            assert ((len(acceptable_skill_names) > 0 and passed_acceptable_skills) or (
                    len(true_sents) > 0 and passed_gold_phrases)), print(
                f"ERROR: see above!")


if __name__ == '__main__':
    main()
