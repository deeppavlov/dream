import requests

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

def check_input_format(test_case) -> bool:
    try:
        errors = []
        if not isinstance(test_case, dict):
            errors.append(f"Invalid type of test_case: {test_case}")
        for key in test_case.keys():
            if key not in input_keys:
                errors.append(f"Invalid input key: {key}")
            if not isinstance(test_case[key], list):
                errors.append(f"Invalid type of input value: {test_case[key]}")
                    
            if key == 'sentences':
                for value in test_case[key]:
                    if not isinstance(value, str):
                        errors.append(f"Invalid value in sentences: {value}")
                    
            if key == 'bot_mood_labels':
                for value in test_case[key]:
                    if value not in values_mood_label:
                        errors.append(f"Invalid value in bot_mood_labels: {value}")
                
            if key == 'bot_emotions':
                for value in test_case[key]:
                    if value not in values_emotion:
                        errors.append(f"Invalid value in bot_emotions: {value}")

            if errors:
                error_message = "; ".join(errors)
                print(f"Input format validation failed: {error_message}")
                return False
            return True

    except Exception as e:
        print(f"Response format validation failed: {e}")
        return False
    
def check_response_format(response: requests.Response) -> bool:
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
            print(f"Response format validation failed: {error_message}")
            return False
        return True

    except Exception as e:
        print(f"Response format validation failed: {e}")
        return False
    
def test():
    test_config = {
        "sentences": ["I will eat pizza"],
        "bot_mood_labels": ["angry"],
        "bot_emotions": ["anger"],
    }
    if check_input_format(test_config):
        print(f"Testing input format - SUCCESS")

    response = requests.post("http://0.0.0.0:8050/respond_batch", json=test_config)
    assert response.status_code == 200

    if check_response_format(response):
        print(f"Testing response format - SUCCESS") 
        print('---' * 30)

    return response

if __name__ == "__main__":
    response = test()
    print(f'Response: {response.text}')