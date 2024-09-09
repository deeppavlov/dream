import requests
import json
import re

def test():
    test_config = {
        "sentences": ["I will eat pizza"],
        "bot_mood_labels": ["angry"],
        "bot_emotions": ["anger"],
    }
    response = requests.post("http://0.0.0.0:8050/respond_batch?profile", json=test_config)
    assert response.status_code == 200
    return response

def count_time(response):
    output_dict = json.loads(response.text)
    total_time = output_dict['duration']

    pattern = r'\"function\": \"send_request_to_prompted_generative_service\".*\"time\": \d.\d+'
    try: 
        new_string = re.search(pattern, response.text)[0]
        new_dict = json.loads('{' + new_string.split(',"children": [{')[0] + '}')
        exec_time = total_time - new_dict['time']

        if exec_time < 0.4:
            print('Testing execution time - SUCCESS')
        print(f'Total time = {total_time :.3f} s (including request to openai)')
        print(f'Execution time = {exec_time :.3f} s (excluding request to openai)')
        print('---' * 30)
        
    except Exception as e:
        raise e

if __name__ == "__main__":
    response = test()
    count_time(response) 