import numpy as np
import pandas as pd
from tqdm import tqdm
from sklearn.metrics import accuracy_score
from colorama import init, Fore

import requests


init(autoreset=True)


def test_accuracy():
    test_data = pd.read_csv('annotators/personality_detection/essays_test.csv')
    traits = ['extraversion', 'neuroticism', 'agreeableness', 'conscientiousness', 'openness']

    for i, row in tqdm(test_data.iterrows(), total=len(test_data)):
        response = requests.post("http://0.0.0.0:8026/model", json={"personality": [row['text']]})
        assert response.status_code == 200
        results = response.json()[0]
        for trait, prediction in results.items():
            test_data.loc[i, trait.lower()+'_pred'] = prediction

    accuracy_per_trait = [accuracy_score(test_data[trait], test_data[trait+'_pred']) for trait in traits]
    avg_accuracy = np.mean(accuracy_per_trait)
    if avg_accuracy * 100 > 56:        
        print('Testing accuracy of classification - SUCCESS')
        print(f'Average accuracy {avg_accuracy :.2%}')
    else:
        print(Fore.RED + f'Average accuracy {avg_accuracy :.2%}')

if __name__ == "__main__":
    test_accuracy()  