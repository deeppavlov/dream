import requests

input_keys = {'user_sentences', 'annotated_utterances', 'sentences', 'bot_mood_labels', 'bot_emotions'}
input_nested_keys = {'emotion_classification', 'sentiment_classification'}
result_nested_keys = {'hypotheses', 'bot_emotion', 'bot_mood'}
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

            if key == 'user_sentences':
                for value in test_case[key]:
                    if not isinstance(value, str):
                        errors.append(f"Invalid value in user_sentences: {value}")
            
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
                                    if nested_key not in input_nested_keys:
                                        errors.append(f"Invalid key in annotations: {nested_key}")
                                    if not isinstance(nested_value, dict):
                                        errors.append(f"Invalid value in annotations: {nested_value}")

                                    if nested_key == 'emotion_classification':
                                        for emotion, proba in nested_value.items():
                                            if emotion not in values_emotion:
                                                errors.append(f"Invalid emotion in emotion_classification: {emotion}")
                                            if proba < 0 or proba > 1:
                                                errors.append(f"Invalid probability in emotion_classification: {proba}")
                                        
                                    if nested_key == 'sentiment_classification':
                                        for sentiment, proba in nested_value.items():
                                            if sentiment not in values_sentiment:
                                                errors.append(f"Invalid sentiment in sentimentn_classification: {sentiment}")
                                            if proba < 0 or proba > 1:
                                                errors.append(f"Invalid probability in sentiment_classification: {proba}")
                    
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

            nested_dict = value[0]
            if not isinstance(nested_dict, dict):
                    errors.append(f"Invalid type of nested_dict: {nested_dict}")

            for nested_key, nested_value in nested_dict.items():
                if nested_key not in result_nested_keys:
                    errors.append(f"Invalid nested_key: {nested_key}")
                else:
                    if nested_key == 'hypotheses':
                        if not isinstance(nested_value, str):
                            errors.append(f"Invalid type of value in hypotheses: {nested_key}")

                    elif nested_key == 'bot_emotion':
                        if nested_value not in values_emotion:
                            errors.append(f"Invalid type of value in bot_emotion: {nested_value}")
                    
                    elif nested_key == 'bot_mood':
                        if nested_value not in values_mood_label:
                            errors.append(f"Invalid type of value in bot_mood: {nested_value}")


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
        "user_sentences": ["What do you want to eat?"],
        "annotated_utterances": [{
            'annotations': {
                'emotion_classification': {'anger': 0.0,
                                            'disgust': 0.0,
                                            'fear': 0.0,
                                            'joy': 0.0,
                                            'neutral': 1.0,
                                            'sadness': 0.0,
                                            'surprise': 0.0},
                'sentiment_classification': {'negative': 0.0,
                                            'neutral': 1.0,
                                            'positive': 0.0}
                            }
                        }],        
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