import os
import requests


SERVICE_PORT = int(os.getenv("SERVICE_PORT"))


def main():
    url = f"http://0.0.0.0:{SERVICE_PORT}/respond"
    input_data = {"sentences": ["джейсон стетхэм хочет есть."]}
    result = requests.post(url, json=input_data).json()
    assert result == [["michal jordan"], ["a white bear"]], print(result)
    print("Success!")


if __name__ == "__main__":
    main()
