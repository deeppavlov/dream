import os
import requests


# N_HYPOTHESES_TO_GENERATE = int(os.environ.get("N_HYPOTHESES_TO_GENERATE", 1))

def test_respond():
    url = "http://0.0.0.0:8189/respond"

    image_paths = ['https://s0.rbk.ru/v6_top_pics/media/img/7/26/346832135841267.jpg']
    print(image_paths)
    sentences = [""]
    print(sentences)

    request_data = {"image_paths": image_paths, "text": sentences}
    result = requests.post(url, json=request_data).json()
    print(result)
    # caption = result['caption'][0][0]['caption']
    # print(caption)
    # obligatory_word = 'bird'

    # result = requests.post(url, json=request_data).json()


    # assert obligatory_word in caption, f"Expected the word '{obligatory_word}' to present in caption"
    print('\n', 'Success!!!')


if __name__ == "__main__":
    test_respond()
