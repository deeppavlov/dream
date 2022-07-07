import requests


url = "http://0.0.0.0:8011/sentseg"
sentences = {"sentences": ["hey alexa how are you"]}

gold = "hey alexa. how are you?"
response = requests.post(url, json=sentences).json()
assert response[0]["punct_sent"] == gold, print(response)

print("SUCCESS!")
