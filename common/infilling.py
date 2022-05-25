import os
import requests


INFILLING_SERVICE_URL = os.getenv("INFILLING_SERVICE_URL", "http://0.0.0.0:8122/respond")


def infill_texts(texts, timeout=1):
    result = requests.post(INFILLING_SERVICE_URL, json={"texts": texts}, timeout=timeout).json()["infilled_text"]
    return result
