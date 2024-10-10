import requests
import time

def main():
    start_time = time.time()
    url = "http://0.0.0.0:8050/respond_batch"
    request_data = {
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