import argparse
import nltk
import pandas as pd
import re
import rouge
import string
from collections import Counter
from typing import List

nltk.data.path.append('/tmp/nltk')
nltk.download('punkt', download_dir='/tmp/nltk')

parser = argparse.ArgumentParser()
parser.add_argument('-pred_f', '--pred_file', type=str)
parser.add_argument('-o', '--output', type=str)


def squad_v1_f1(y_true: List[List[str]], y_predicted: List[str]) -> float:
    """ Calculates F-1 score between y_true and y_predicted
        F-1 score uses the best matching y_true answer

        Skips examples without an answer.
    Args:
        y_true: list of correct answers (correct answers are represented by list of strings)
        y_predicted: list of predicted answers
    Returns:
        F-1 score : float
    """
    f1_total = 0.0
    count = 0
    for ground_truth, prediction in zip(y_true, y_predicted):
        if len(ground_truth[0]) == 0:
            # skip empty answers
            continue
        count += 1
        prediction_tokens = normalize_answer(prediction).split()
        f1s = []
        for gt in ground_truth:
            gt_tokens = normalize_answer(gt).split()
            common = Counter(prediction_tokens) & Counter(gt_tokens)
            num_same = sum(common.values())
            if num_same == 0:
                f1s.append(0.0)
                continue
            precision = 1.0 * num_same / len(prediction_tokens)
            recall = 1.0 * num_same / len(gt_tokens)
            f1 = (2 * precision * recall) / (precision + recall)
            f1s.append(f1)
        f1_total += max(f1s)
    return 100 * f1_total / count if count > 0 else 0


def normalize_answer(s: str) -> str:
    def remove_articles(text):
        return re.sub(r'\b(a|an|the)\b', ' ', text)

    def white_space_fix(text):
        return ' '.join(text.split())

    def remove_punc(text):
        exclude = set(string.punctuation)
        return ''.join(ch for ch in text if ch not in exclude)

    def lower(text):
        return text.lower()

    return white_space_fix(remove_articles(remove_punc(lower(s))))


def main():
    args = parser.parse_args()
    data = pd.read_excel(args.pred_file, sheet_name=None, header=None, names=['Sentence', 'Correct_answer', 'Answer'])
    # select sheet with factoid questions
    # todo make as argument
    data = data['factoid']
    evaluator = rouge.Rouge(metrics=['rouge-n', 'rouge-l'],
                            max_n=4,
                            limit_length=True,
                            length_limit=100,
                            length_limit_type='words',
                            apply_avg=True,
                            apply_best=False,
                            alpha=0.5,  # Default F1_score
                            weight_factor=1.2,
                            stemming=True)

    with open(args.output, 'w') as fout:
        ground_truth = [str(el) for el in data['Correct_answer'].values]
        predicted = [str(el) for el in data['Answer'].values]
        squad_f1 = squad_v1_f1([[el] for el in ground_truth], predicted)
        scores = evaluator.get_scores(predicted, ground_truth)
        fout.write(f'squad f1: {squad_f1:.3f}\n')
        for m in scores:
            fout.write(f'{m}:  p: {scores[m]["p"]:.3f} r: {scores[m]["r"]:.3f} f: {scores[m]["f"]:.3f}\n')


if __name__ == '__main__':
    main()
