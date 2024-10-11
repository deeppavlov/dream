import requests
import time
import subprocess
import allure
import json

url = "http://0.0.0.0:8045/respond"

@allure.description("""4.1.2 Test input and output data types""")
def test_in_out():
    video_path = "http://files:3000/file?file=file_228.mp4"
    test_data = { "paths": [video_path]}
    result = requests.post(url, json=test_data)
    valid_extensions = ['.mp4']
    assert any(url.lower().endswith(ext) for ext in valid_extensions), "Invalid input type"

@allure.description("""4.1.3 Test execution time""")
def test_exec_time():
    video_path = "http://files:3000/file?file=file_228.mp4"
    test_data = { "paths": [video_path]}
    start_time = time.time()
    result = requests.post(url, json=test_data)
    assert time.time() - start_time <= 0.4, "Unsufficient run time"

@allure.description("""4.2.2 Test launch time""")
def test_launch_time():
    video_path = "http://files:3000/file?file=file_228.mp4"
    test_data = { "paths": [video_path]}
    start_time = time.time()
    response = False
    while True:
        try:
            current_time = time.time()
            response = requests.post(url, json=test_data).status_code == 200
            if response:
                break
        except Exception as e:
            print(f"Exception occurred: {e}")
            current_time = time.time()
            if current_time - start_time < 20 * 60:  # < 20 minutes
                time.sleep(15)
                continue
            else:
                break
    assert response

@allure.description("""4.3.3 Test rights for dream""")
def test_rights():
    command = "groups $(whoami) | grep -o 'docker'"
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert result.returncode == 0, f"Executed with error: {result.stderr}"
    assert 'dolidze' in result.stdout, "Group 'dolidze' not found"

@allure.description("""Simple execution test""")
def test_execution():
    video_path = "http://files:3000/file?file=file_228.mp4"
    gold_result = json.loads("[{'sentence': 'Intro.', 'timestamp': [0.0, 10.727636363636364]}, {'sentence': 'Showing impressive award combinations.', 'timestamp': [10.727636363636364, 30.3949696969697]}, {'sentence': 'Discussing who won an Oscar and a gold medal.', 'timestamp': [30.3949696969697, 59.002]}]")
    test_data = { "paths": [video_path]}
    result = requests.post(url, json=test_data)
    assert result.json() == gold_result

if __name__ == "__main__":
    test_in_out()
    test_exec_time()
    test_launch_time()
    # test_rights()
    # test_execution()