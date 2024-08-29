import json
import requests
import time

from typing import Dict, Any
from colorama import init, Fore


init(autoreset=True)


class TestCases:
    input_keys = {'sentences', 'annotated_utterances', 'bot_mood'}
    input_nested_keys = {'emotion_classification', 'sentiment_classification'}
    result_keys = {"bot_emotion", "bot_mood", "bot_mood_label"}
    values_emotion = {
            'anger', 
            'resentment', 
            'disappointment', 
            'disgust', 'shame', 
            'distress', 
            'fear', 
            'sadness', 
            'admiration', 
            'joy', 
            'liking', 
            'love', 
            'surprise', 
            'gratitude', 
            'pride', 
            'relief', 
            'pity', 
            'neutral'
        }
    values_sentiment = {
            'negative', 
            'neutral', 
            'positive', 
        }
    result_values_mood_label = {
            'happy', 
            'dependent', 
            'angry', 
            'disdainful', 
            'sad', 
            'docile', 
            'relaxed', 
            'fear', 
            'neutral'
        }
    timeout = 0.4

    def __init__(self, url: str, test_cases: list) -> None:
        self.url = url
        self.test_cases = test_cases
        self.metrics = {
            'total_requests': 0,
            'total_time': 0.0,
            'timeout_per_case' : 0,
            'input_format' : 0,
            'response_format' : 0
        }

    def _post(self, data: Dict[str, Any]) -> requests.Response:
        return requests.post(self.url, json=data)
    
    def _check_input_format(self, test_case) -> bool:
        try:
            errors = []
            if not isinstance(test_case, dict):
                errors.append(f"Invalid type of test_case: {test_case}")
            for key in test_case.keys():
                if key not in self.input_keys:
                    errors.append(f"Invalid input key: {key}")
                if not isinstance(test_case[key], list):
                    errors.append(f"Invalid type of input value: {test_case[key]}")
                
                if key == 'sentences':
                    for value in test_case[key]:
                        if not isinstance(value, str):
                            errors.append(f"Invalid value in sentences: {value}")
                
                if key == 'annotated_utterances':
                    for value in test_case[key]:
                        if not isinstance(value, dict):
                            errors.append(f"Invalid value in annotated_utterances: {value}")
                        else:
                            for key_ in value.keys():
                                if key_ != 'annotations':
                                    errors.append(f"Invalid key in annotated_utterances: {key_}")
                                else:
                                    nested_dict = value['annotations']
                                    for nested_key, nested_value in nested_dict.items():
                                        if nested_key not in self.input_nested_keys:
                                            errors.append(f"Invalid key in annotations: {nested_key}")
                                        if not isinstance(nested_value, dict):
                                            errors.append(f"Invalid value in annotations: {nested_value}")

                                        if nested_key == 'emotion_classification':
                                            for emotion, proba in nested_value.items():
                                                if emotion not in self.values_emotion:
                                                    errors.append(f"Invalid emotion in emotion_classification: {emotion}")
                                                if proba < 0 or proba > 1:
                                                    errors.append(f"Invalid probability in emotion_classification: {proba}")
                                        
                                        if nested_key == 'sentiment_classification':
                                            for sentiment, proba in nested_value.items():
                                                if sentiment not in self.values_sentiment:
                                                    errors.append(f"Invalid sentiment in sentimentn_classification: {sentiment}")
                                                if proba < 0 or proba > 1:
                                                    errors.append(f"Invalid probability in sentiment_classification: {proba}")
                
                if key == 'bot_mood':
                    for value in test_case[key]:
                        if not isinstance(value, list):
                            errors.append(f"Invalid value in bot_mood: {value}")
                        else:
                            for dim in value:
                                if dim < -1 or dim > 1:
                                    errors.append(f"Invalid dimension in bot_mood: {dim}")                   

            if errors:
                error_message = "; ".join(errors)
                print(Fore.RED + f"Input format validation failed: {error_message}")
                return False
            return True

        except Exception as e:
            print(f"Response format validation failed: {e}")
            return False

    def _check_response_status(self, response: requests.Response) -> bool:
        if response.status_code == 200:
            return True
        else:
            return False

    def _check_response_format(self, response: requests.Response) -> bool:
        try:
            errors = []
            for key, value in response.json()[0].items():
                if key not in self.result_keys:
                    errors.append(f"Invalid key: {key}")

                if key == 'bot_emotion' and value not in self.values_emotion:
                    errors.append(f"Invalid value: bot_emotion - {value}")
                
                if key == 'bot_mood':
                    for i, dim in enumerate(value):
                        if dim < -1 or dim > 1:
                            errors.append(f"Invalid value: bot_mood {i} - {dim}")

                if key == 'bot_mood_label' and value not in self.result_values_mood_label:
                    errors.append(f"Invalid value: bot_mood_label - {value}")

            if errors:
                error_message = "; ".join(errors)
                print(Fore.RED + f"Response format validation failed: {error_message}")
                return False
            return True

        except Exception as e:
            print(Fore.RED + f"Response format validation failed: {e}")
            return False

    def _run_test(self, test_case: Dict[str, Any], index: int) -> None:
        start_time = time.time()
        try:
            response = self._post(test_case)
            elapsed_time = time.time() - start_time
            self.metrics['total_requests'] += 1
            self.metrics['total_time'] += elapsed_time

            status_ok = self._check_response_status(response)
            if status_ok:
                input_format_ok = self._check_input_format(test_case)
                if input_format_ok:
                    self.metrics['input_format'] += 1

                if elapsed_time < self.timeout:
                    self.metrics['timeout_per_case'] += 1                
                
                response_format_ok = self._check_response_format(response)              
                if response_format_ok:
                    self.metrics['response_format'] += 1

        except Exception as e:
            print(Fore.RED + f"Test case {index} failed: {e}")

    def run_tests(self) -> None:
        for index, test_case in enumerate(self.test_cases):
            self._run_test(test_case, index)

        average_time = (self.metrics['total_time'] / self.metrics['total_requests']) if self.metrics['total_requests'] > 0 else 0
        print(f"Total requests: {self.metrics['total_requests']}")
        print(f"Average response time: {average_time:.3f} s")
        if self.metrics['timeout_per_case'] == len(self.test_cases):
            print(f'Testing response time per case - SUCCESS')
        if self.metrics['input_format'] == len(self.test_cases):
            print(f"Testing input format - SUCCESS")
        if self.metrics['response_format'] == len(self.test_cases):
            print(f"Testing response format - SUCCESS")

if __name__ == "__main__":
    with open('annotators/bot_emotion_classifier/test_cases.json', 'r') as f:
        test_cases = json.load(f)

    tester = TestCases("http://0.0.0.0:8051/model", test_cases)
    tester.run_tests()
