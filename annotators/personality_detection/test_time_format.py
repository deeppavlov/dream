import json
import requests
import time

from typing import Dict, Any, List
from colorama import init, Fore


init(autoreset=True)


class TestCases:
    result_keys = {"EXTRAVERSION", "NEUROTICISM", "AGREEABLENESS", "CONSCIENTIOUSNESS", "OPENNESS"}
    result_values = {0, 1}
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
            if not isinstance(test_case, list):
                errors.append(f"Invalid test_case: {test_case}")
            for value in test_case:
                if not isinstance(value, str):
                    errors.append(f"Invalid value in test_case: {value}")

            if errors:
                error_message = "; ".join(errors)
                print(Fore.RED + f"Input format validation failed: {error_message}")
                return False
            return True

        except Exception as e:
            print(Fore.RED + f"Input format validation failed: {e}")
            return False

    def _check_response_status(self, response: requests.Response) -> bool:        
        if response.status_code == 200:
            return True
        else:
            return False

    def _check_response_format(self, response: requests.Response) -> bool:
        try:
            errors = []
            for response_json in response.json():
                for key, value in response_json.items():
                    if key not in self.result_keys:
                        errors.append(f"Invalid key: {key}")
                    if value not in self.result_values:
                        errors.append(f"Invalid value: {value}")

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
            response = self._post({"personality": test_case})
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
    with open('annotators/personality_detection/test_cases.json', 'r') as f:
        test_data = json.load(f)
    test_cases = [data['sentences'] for data in test_data]

    tester = TestCases("http://0.0.0.0:8026/model", test_cases)
    tester.run_tests()
