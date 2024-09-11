import requests
import time

def main():
    start_time = time.time()
    url = "http://0.0.0.0:8051/model"
    request_data = {
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
        'bot_mood': [[0.0, 0.0, 0.0]]
        }
    
    trials = 0
    response = 104
    while response != 200:
        try:
            response = requests.post(url, json=request_data).status_code
    
        except Exception as e:
            time.sleep(2)
            trials += 1
            if trials > 600:
                raise TimeoutError("Couldn't build the component")

    total_time = time.time() - start_time
    print('---' * 30)
    if total_time < 1200:
        print("Testing launch time - SUCCESS")
    print(f"Launch time = {total_time:.3f}s")
    print('---' * 30)

if __name__ == "__main__":
    main()