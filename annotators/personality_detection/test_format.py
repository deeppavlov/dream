import requests

result_keys = {"traits", "traits_proba"}
result_trait_keys = {"EXTRAVERSION", "NEUROTICISM", "AGREEABLENESS", "CONSCIENTIOUSNESS", "OPENNESS"}

def check_input_format(test_case) -> bool:
    try:
        errors = []
        if not isinstance(test_case, dict):
            errors.append(f"Invalid test_case: {test_case}")
        else:
            for key, value in test_case.items():
                if key != 'personality':
                    errors.append(f"Invalid key in test_case: {key}")
                if not isinstance(value, list):
                    errors.append(f"Invalid value in test_case: {value}")
                for el in value:
                    if not isinstance(el, str):
                        errors.append(f"Invalid value in test_case: {el}")

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
        for response_json in response.json():
            for key, value in response_json.items():
                if key not in result_keys:
                    errors.append(f"Invalid key: {key}")
                if not isinstance(value, dict):
                    errors.append(f"Invalid type of value: {value}")

                if key == 'traits':
                    nested_dict = value
                    for nested_key, nested_value in nested_dict.items():
                        if nested_key not in result_trait_keys:
                            errors.append(f"Invalid nested_key: {nested_key}")
                        if nested_value not in {0, 1}:
                            errors.append(f"Invalid nested_value: {nested_value}")
                
                if key == 'traits_proba':
                    nested_dict = value
                    for nested_key, nested_value in nested_dict.items():
                        if nested_key not in result_trait_keys:
                            errors.append(f"Invalid nested_key: {nested_key}")
                        if not isinstance(nested_value, list):
                            errors.append(f"Invalid type of nested_value: {nested_value}")
                        else:
                            for proba in nested_value:
                                if proba < 0 or proba > 1:
                                    errors.append(f"Invalid proba: {proba}")

        if errors:
            error_message = "; ".join(errors)
            print(f"Response format validation failed: {error_message}")
            return False
        return True
    
    except Exception as e:
        print(f"Response format validation failed: {e}")
        return False
    
def test():
    test_config = {"personality": ["Yeah that would be cool!"]}

    if check_input_format(test_config):
        print(f"Testing input format - SUCCESS")

    response = requests.post("http://0.0.0.0:8026/model", json=test_config)
    assert response.status_code == 200

    if check_response_format(response):
        print(f"Testing response format - SUCCESS") 

    return response

if __name__ == "__main__":
    response = test()
    print(f'Response: {response.text}')
    print('---' * 30)


