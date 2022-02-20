import json
import requests


URL = f"http://0.0.0.0:8121/respond"

utterances = [[
    "Yeah I think the original is going to be the best. Did you know that Stephen King actually thinks that the "
    "movie Bambi should be a horror movie?",
    "He was traumatized as a child. That movie did have death. so it could be scary. Anyway. "
    "he turned his trauma into a career.",
    "Well that's really good for him! Do you think that horror movies actually burn almost 200 calories per movie? "
    "If so I should watch more to lose weight LOL"
]]

with open("test_midas_distributions.json", "r") as f:
    midas_distributions = json.load(f)


if __name__ == "__main__":

    requested_data = {"utterances": utterances, "midas_distributions": midas_distributions}
    result = requests.post(URL, json=requested_data).json()
    print(result)
    print("Success")
