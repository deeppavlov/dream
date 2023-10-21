import requests
from time import time


def main_test():
    url = "http://0.0.0.0:8218/model"
    configs = [{"sentences":["what is saas marketing"],"answers_dnnc":["oos"]},
               {"sentences":["what day is it gonna be in twenty-one days"],
                "answers_dnnc":["date"]},
               {"sentences":["how long will it take me to make baked chicken"],
                "answers_dnnc":["cook_time"]}]
    t = time()
    for config in configs:
        responses = requests.post(url, json=config).json()
        for response, answer, sentence in zip(responses, config["answers_dnnc"], config["sentences"]):
            #  print((response, answer, sentence))
            predicted_classes = [class_ for class_ in response if response[class_] == max(response.values())]
            assert sorted(answer) == sorted(predicted_classes), " * ".join(
                [str(j) for j in [sentence, answer, predicted_classes, response]]
            )
    print("SUCCESS!")
    print(time() - t)
    return 0


main_test()
