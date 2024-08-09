import requests
import time

def main():
    start_time = time.time()
    url = "http://0.0.0.0:8136/respond"
    request_data = {"utterances": [["i live in moscow"]]}
    
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
    print("Success")
    print(f"property extraction launch time = {total_time:.3f}s")

if __name__ == "__main__":
    main()