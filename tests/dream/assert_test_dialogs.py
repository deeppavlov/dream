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
        true_sents = set([sent.lower().replace('\n', ' ') for sent in true_r[1:]])
        assert skill != "exception", print("ERROR: exception in gold phrases".format(pred_r[-1], true_sents))
        if true_sents:
            checked = False
            for true_sent in true_sents:
                if true_sent in pred_r[-1].lower().replace('\n', ' '):
                    checked = True
            assert checked, print("ERROR: {} not in {}".format(pred_r[-1], true_sents))


if __name__ == '__main__':
    main()
