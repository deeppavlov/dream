import requests


url = "http://0.0.0.0:8011/sentseg"
sentences = {"sentences": ["привет как дела"]}

gold = "привет. как дела?"
segments_gold = ["привет.", "как дела?"]

response = requests.post(url, json=sentences).json()

assert response[0]["punct_sent"] == gold, print(response)
assert response[0]["segments"] == segments_gold, print(response)

print("SUCCESS!")
