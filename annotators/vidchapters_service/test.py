import os
import requests

import allure
import pytest
import subprocess

import time

@allure.description("""4.2.2 Test launch time""")
@pytest.mark.parametrize(
    "video_path, gold_result",
    [
        (
            "http://files:3000/file?file=file_228.mp4",
            "[{'sentence': 'Intro.', 'timestamp': [0.0, 10.727636363636364]}, {'sentence': 'Showing impressive award combinations.', 'timestamp': [10.727636363636364, 30.3949696969697]}, {'sentence': 'Discussing who won an Oscar and a gold medal.', 'timestamp': [30.3949696969697, 59.002]}]\n",
        ),
    ]
)
def test_text_qa_launch_time(video_path, gold_result):
    start_time = time.time()
    response = False

    while True:
        try:
            current_time = time.time()
            response = get_answer(video_path).status_code == 200
            if response:
                break

        except Exception as e:
            current_time = time.time()
            if current_time - start_time < 20 * 60: # < 20 minutes
                time.sleep(15)
                continue
            else:
                break
    assert response 


@allure.description("""4.1.3 Test execution time""")
@pytest.mark.parametrize(
    "video_path, gold_result",
    [
        (
            "http://files:3000/file?file=file_228.mp4",
            "[{'sentence': 'Intro.', 'timestamp': [0.0, 10.727636363636364]}, {'sentence': 'Showing impressive award combinations.', 'timestamp': [10.727636363636364, 30.3949696969697]}, {'sentence': 'Discussing who won an Oscar and a gold medal.', 'timestamp': [30.3949696969697, 59.002]}]\n",
        ),
    ]
)
def test_text_qa_exec_time(video_path):
    start_time = time.time()
    result = get_answer(video_path)
    assert time.time() - start_time <= 0.4

@allure.description("""4.1.2 Test output data type""")
@pytest.mark.parametrize(
    "video_path, gold_result",
    [
        (
            "http://files:3000/file?file=file_228.mp4",
            "[{'sentence': 'Intro.', 'timestamp': [0.0, 10.727636363636364]}, {'sentence': 'Showing impressive award combinations.', 'timestamp': [10.727636363636364, 30.3949696969697]}, {'sentence': 'Discussing who won an Oscar and a gold medal.', 'timestamp': [30.3949696969697, 59.002]}]\n",
        ),
    ]
)
def test_text_qa_json(video_path, gold_result):
    start_time = time.time()
    result = get_answer(video_path)
    try:
        result.json()
        assert True
    except Exception as e:
        assert False


@allure.description("""4.3.3 Test roles for docker""")
def test_roles():
    command = "groups $(whoami) | grep -o 'docker'"
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert result.returncode == 0, f"Executed with error: {result.stderr}"
    assert 'docker' in result.stdout, "Group 'docker' not found"




@allure.description("""Test execution""")
@pytest.mark.parametrize(
    "video_path, gold_result",
    [
        (
            {
                "http://files:3000/file?file=file_228.mp4"
            },
            "[{'sentence': 'Intro.', 'timestamp': [0.0, 10.727636363636364]}, {'sentence': 'Showing impressive award combinations.', 'timestamp': [10.727636363636364, 30.3949696969697]}, {'sentence': 'Discussing who won an Oscar and a gold medal.', 'timestamp': [30.3949696969697, 59.002]}]\n"
        ),
        (
            {
                'http://files:3000/file?file=file_219.mp4'
            },
            "[{\'sentence\': \'Intro.\', \'timestamp\': [0.0, 4.0707879090909085]}, {\'sentence\': \'Getting the diver ready.\', \'timestamp\': [4.0707879090909085, 12.664673494949495]}, {\'sentence\': \"Showing emma webber\'s cap.\", \'timestamp\': [12.664673494949495, 32.56630327272727]}, {\'sentence\': \'Will emma keep the cap.\', \'timestamp\': [32.56630327272727, 35.732471646464646]}, {\'sentence\': \'Outro.\', \'timestamp\': [35.732471646464646, 44.778667]}]\n"
        ),
    ],
)
def test_exec(video_path, gold_result):
    result = requests.post("http://0.0.0.0:8045/model", json=video_path)
    assert result.ok
    assert result.json() == gold_result
    print("SUCCESS")