import requests


def test_knowledge_grounding():
    url = 'http://0.0.0.0:8083/respond'

    checked_sentence1 = 'When Mabel visited their home to play the piano, ' \
                        'she occasionally glimpsed a flitting swirl of white in the next room, ' \
                        'sometimes even received a note of thanks for calling, but she never actually ' \
                        'spoke with the reclusive, almost spectral Emily.'
    knowledge1 = 'The real-life soap opera behind the publication of Emily Dickinson’s poems\n' \
                 'When Mabel visited their home to play the piano, she occasionally glimpsed ' \
                 'a flitting swirl of white in the next room, sometimes even received a note of ' \
                 'thanks for calling, but she never actually spoke with the reclusive, almost spectral Emily.'
    text1 = 'Yeah she was an icon she died in 1886 at the tender age of 55.'

    checked_sentence2 = 'Penguins are a group of aquatic flightless birds.'
    knowledge2 = 'Penguins are a group of aquatic flightless birds.'
    text2 = 'Who are penguins?'

    history = 'Do you know who Emily Dickson is?\n' \
              'Emily Dickinson? The poet? I do! "Tell all the truth, but tell it slant" ' \
              'she once said. Do you like her poetry?'

    request_data = {
        'batch': [
            {
                'checked_sentence': checked_sentence1,
                'knowledge': knowledge1,
                'text': text1,
                'history': history
            },
            {
                'checked_sentence': checked_sentence2,
                'knowledge': knowledge2,
                'text': text2,
                'history': history
            }

        ]
    }
    results = requests.post(url, json=request_data).json()
    assert all(results), f'Got empty string among results'
    print('Got\n{}\nSuccess'.format(results))


if __name__ == '__main__':
    test_knowledge_grounding()
