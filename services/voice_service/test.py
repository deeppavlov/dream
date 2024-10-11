# import requests


# def test_respond():
#     url = "http://0.0.0.0:8333/respond"

#     # voice_path = "..."

#     contexts = [["hi", "hi. how are you?"], ["let's chat about movies", "cool. what movies do you like?"]]
#     gold_result = [["Reacting to a voice message "]]
#     result = requests.post(url, json={"utterances_histories": contexts}).json()
#     assert [
#         len(sample[0]) > 0 and all([len(text) > 0 for text in sample[0]]) and all([conf > 0.0 for conf in sample[1]])
#         for sample in result
#     ], f"Got\n{result}\n, but expected:\n{gold_result}"


# if __name__ == "__main__":
#     test_respond()

import requests
import time
import subprocess
import allure
import json

url = "http://0.0.0.0:8333/respond"

@allure.description("""4.1.2 Test input and output data types""")
def test_in_out():
    sound_paths = "http://files:3000/file?file=file_50.oga"
    # video_paths = "http://files:3000/file?file=file_228.mp4"
    sound_durations = 5
    sound_types = 'oga'
    test_data = { "paths": [sound_paths], "durations": [sound_durations], "types": [sound_types]}
    result = requests.post(url, json=test_data)
    valid_extensions = [".oga", ".mp3", ".MP3", ".ogg", ".flac", ".mp4"]
    assert any(url.lower().endswith(ext) for ext in valid_extensions), "Invalid input type"

@allure.description("""4.1.3 Test execution time""")
def test_exec_time():
    sound_paths = "http://files:3000/file?file=file_50.oga"
    # video_paths = "http://files:3000/file?file=file_228.mp4"
    sound_durations = 5
    sound_types = 'oga'
    test_data = { "paths": [sound_paths], "durations": [sound_durations], "types": [sound_types]}
    start_time = time.time()
    result = requests.post(url, json=test_data)
    assert time.time() - start_time <= 0.4, "Unsufficient run time"

@allure.description("""4.2.2 Test launch time""")
def test_launch_time():
    sound_paths = "http://files:3000/file?file=file_50.oga"
    # video_paths = "http://files:3000/file?file=file_228.mp4"
    sound_durations = 5
    sound_types = 'oga'
    test_data = { "paths": [sound_paths], "durations": [sound_durations], "types": [sound_types]}
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

if __name__ == "__main__":
    test_in_out()
    test_exec_time()
    test_launch_time()
    # test_rights()
    # test_execution()
