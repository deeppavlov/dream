import requests

input_keys = {'sentences', 'annotated_utterances', 'bot_mood', 'bot_personality'}
input_nested_keys = {'emotion_classification', 'sentiment_classification'}
result_keys = {"bot_emotion", "bot_emotion_proba", "bot_mood", "bot_mood_label"}
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
keys_personality = {
            'extraversion',
            'agreeableness',
            'conscientiousness',
            'neuroticism',
            'openness'
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
                
            if key == 'bot_mood':
                for value in test_case[key]:
                    if not isinstance(value, list):
                        errors.append(f"Invalid value in bot_mood: {value}")
                    else:
                        for dim in value:
                            if dim < -1 or dim > 1:
                                errors.append(f"Invalid dimension in bot_mood: {dim}")

            if key == 'bot_personality':
                for value in test_case[key]:
                    if not isinstance(value, dict):
                        errors.append(f"Invalid value in bot_personality: {value}")
                    else:
                        for trait, trait_value in value.items():
                            if trait not in keys_personality:
                                errors.append(f"Invalid trait in bot_personality: {trait}")
                            if trait_value < 0 or trait_value > 1:
                                errors.append(f"Invalid trait_value in bot_personality: {dim}")

        if errors:
            error_message = "; ".join(errors)
            print(f"Input format validation failed: {error_message}")
            return False
        return True

    except Exception as e:
        print(f"Input format validation failed: {e}")
        return False

def check_response_format(response: requests.Response) -> bool:
    try:
        errors = []
        for key, value in response.json()[0].items():
            if key not in result_keys:
                errors.append(f"Invalid key: {key}")

            if key == 'bot_emotion' and value not in values_emotion:
                errors.append(f"Invalid value: bot_emotion - {value}")

            if key == 'bot_emotion_proba':
                for emotion, proba in value.items():
                    if emotion not in values_emotion:
                        errors.append(f"Invalid emotion in bot_emotion_proba: {emotion}")
                    if proba < 0 or proba > 1:
                        errors.append(f"Invalid proba in bot_emotion_proba: {proba}")
                
            if key == 'bot_mood':
                for i, dim in enumerate(value):
                    if dim < -1 or dim > 1:
                        errors.append(f"Invalid value: bot_mood {i} - {dim}")

            if key == 'bot_mood_label' and value not in values_mood_label:
                errors.append(f"Invalid value: bot_mood_label - {value}")

        if errors:
            error_message = "; ".join(errors)
            print(f"Response format validation failed: {error_message}")
            return False
        return True

    except Exception as e:
        print(f"Response format validation failed: {e}")
        return False

def test(test_config):
    if check_input_format(test_config):
        print(f"Testing input format - SUCCESS")

    response = requests.post("http://0.0.0.0:8051/model", json=test_config)
    assert response.status_code == 200

    if check_response_format(response):
        print(f"Testing response format - SUCCESS") 

    return response

if __name__ == "__main__":
    test_config = {
        'sentences': [' Yeah that would be cool ! '],
        'annotated_utterances': [{
            'annotations': {
                'emotion_classification': {'anger': 0.0,
                                            'disgust': 0.0,
                                            'fear': 0.0,
                                            'joy': 0.94,
                                            'neutral': 0.05,
                                            'sadness': 0.0,
                                            'surprise': 0.01},
                'sentiment_classification': {'negative': 0.01,
                                            'neutral': 0.88,
                                            'positive': 0.1}
                            }
                        }],
        'bot_mood': [[0.0, 0.0, 0.0]],
        'bot_personality': [{
            'extraversion': 0.89,
            'agreeableness': 0.92,
            'conscientiousness': 0.86,
            'neuroticism': 0.11,
            'openness': 0.23
            }]
        }
    print('---' * 30)
    response = test(test_config)
    print(f'\nInput: {test_config}\n')
    print(f'Response: {response.text}')
    print('---' * 30)
