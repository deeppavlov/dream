import json
import requests
import time

from typing import Dict, Any, List

class TestCases:
    timeout = 0.4

    def __init__(self, url: str, test_cases: list) -> None:
        self.url = url
        self.test_cases = test_cases
        self.metrics = {
            'total_requests': 0,
            'total_time': 0.0,
            'time_per_case' : 0.0,
        }

    def _post(self, data: Dict[str, Any]) -> requests.Response:
        return requests.post(self.url, json=data)

    def _run_test(self, test_case: List[str], index: int) -> None:
        start_time = time.time()
        try:
            response = self._post({"personality": test_case})
            elapsed_time = time.time() - start_time
            self.metrics['total_requests'] += 1
            self.metrics['total_time'] += elapsed_time
            assert response.status_code == 200

            if elapsed_time < self.timeout:
                self.metrics['time_per_case'] += 1          

        except Exception as e:
            print(f"Test case {index} failed: {e}")

    def run_tests(self) -> None:
        for index, test_case in enumerate(self.test_cases):
            self._run_test(test_case, index)

        if self.metrics['time_per_case'] == len(self.test_cases):
            print(f'Testing response time per case - SUCCESS')
        average_time = (self.metrics['total_time'] / self.metrics['total_requests']) if self.metrics['total_requests'] > 0 else 0
        print(f"Total requests: {self.metrics['total_requests']}")
        print(f"Average response time: {average_time:.3f} s")
        print('---' * 30)

if __name__ == "__main__":
    with open('annotators/personality_detection/test_cases.json', 'r') as f:
        test_data = json.load(f)
    test_cases = [data['sentences'] for data in test_data]

    tester = TestCases("http://0.0.0.0:8026/model", test_cases)
    tester.run_tests()
