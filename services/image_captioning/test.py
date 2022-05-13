import requests
import os

def test_respond():
    url = "http://0.0.0.0:8123/respond"

    img_paths = ['examples/dog.jpg',
                 'examples/bird.jpg',
                 'examples/cows.jpg']

    request_data = {"text": img_paths}

    result = requests.post(url, json=request_data).json()

    captions = [img[0]['caption'] for img in result['caption']]
    captions_obligatory_words = ['dog', 'bird', 'cow']

    for idx, caption in enumerate(captions):
        print(idx, ':', caption)
        oblig_word = captions_obligatory_words[idx]
        assert oblig_word in caption, f"Expected the word '{oblig_word}' to present in caption for image {idx}"

    print('\n', 'Success!!!')


if __name__ == "__main__":
    test_respond()