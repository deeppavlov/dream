import argparse
import csv
import statistics


parser = argparse.ArgumentParser()
parser.add_argument('-pred_f', '--pred_file', type=str)
parser.add_argument('-true_f', '--true_file', type=str)


def main():
    args = parser.parse_args()

    pred_data = []
    with open(args.pred_file, 'r', newline='') as f:
        reader = csv.reader(f, delimiter=' ')
        pred_data = [row[-4:] for row in reader][1:]

    true_data = []
    with open(args.true_file, 'r', newline='') as f:
        reader = csv.reader(f, delimiter=' ')
        true_data = [row for row in reader][1:]
    proc_times = [float(r[0]) for r in pred_data]
    mean_proc_time = statistics.mean(proc_times)

    assert statistics.mean(proc_times) <= 4, print(f'Mean proc time: {mean_proc_time}')

    for pred_r, true_r in zip(pred_data, true_data):
        true_sents = set([sent.lower() for sent in true_r[1:]])
        if true_sents:
            assert pred_r[-1].lower() in true_sents, print("ERROR: {} not in {}".format(pred_r[-1], true_sents))



if __name__ == '__main__':
    main()
