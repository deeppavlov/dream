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

    assert statistics.mean(proc_times) <= 3

    for pred_r, true_r in zip(pred_data, true_data):
        assert pred_r[-1].lower() == true_r[-1].lower(), \
               print("ERROR: {} !== {}".format(pred_r[-1], true_r[-1]))



if __name__ == '__main__':
    main()
