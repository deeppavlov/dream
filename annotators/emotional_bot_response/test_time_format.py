import requests
import time

from typing import Dict, Any, List
from colorama import init, Fore

init(autoreset=True)

class TestCases:
    input_keys = {'sentences', 'bot_mood_labels', 'bot_emotions'}
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
    values_mood_label = {
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
                    
                if key == 'bot_mood_labels':
                    for value in test_case[key]:
                        if value not in self.values_mood_label:
                            errors.append(f"Invalid value in bot_mood_labels: {value}")
                
                if key == 'bot_emotions':
                    for value in test_case[key]:
                        if value not in self.values_emotion:
                            errors.append(f"Invalid value in bot_emotions: {value}")

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
                if key != "batch":
                    errors.append(f"Invalid key: {key}")
                if not isinstance(value, list):
                    errors.append(f"Invalid value: {value}")

                for value_ in value:
                    if not isinstance(value_, dict):
                        errors.append(f"Invalid type of value: {value_}")
                    else:
                        for nested_key, nested_value in value_.items():
                            if nested_key != "hypotheses":
                                errors.append(f"Invalid nested key: {nested_key}")
                            if not isinstance(nested_value, str):
                                errors.append(f"Invalid nested value: {nested_value}")

            if errors:
                error_message = "; ".join(errors)
                print(Fore.RED + f"Response format validation failed: {error_message}")
                return False
            return True

        except Exception as e:
            print(Fore.RED + f"Response format validation failed: {e}")
            return False

    def _run_test(self, test_case: List[str], index: int) -> None:
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
    test_config = {
        "sentences": ["I will eat pizza"],
        "bot_mood_labels": ["angry"],
        "bot_emotions": ["anger"],
    }
    test_cases = [test_config]

    tester = TestCases("http://0.0.0.0:8050/respond_batch", test_cases)
    tester.run_tests()