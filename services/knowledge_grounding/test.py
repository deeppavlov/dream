import requests


def test_knowledge_grounding():
    url = 'http://0.0.0.0:8083/respond'

    checked_sentence = 'When Mabel visited their home to play the piano, ' \
                       'she occasionally glimpsed a flitting swirl of white in the next room, ' \
                       'sometimes even received a note of thanks for calling, but she never actually ' \
                       'spoke with the reclusive, almost spectral Emily.'
    knowledge = 'The real-life soap opera behind the publication of Emily Dickinson’s poems\n' \
                'When Mabel visited their home to play the piano, she occasionally glimpsed ' \
                'a flitting swirl of white in the next room, sometimes even received a note of ' \
                'thanks for calling, but she never actually spoke with the reclusive, almost spectral Emily.'
    text = 'Yeah she was an icon she died in 1886 at the tender age of 55.'
    history = 'Do you know who Emily Dickson is?\n' \
              'Emily Dickinson? The poet? I do! "Tell all the truth, but tell it slant" ' \
              'she once said. Do you like her poetry?'

    request_data = {
        'batch': [
            {
                'checked_sentence': checked_sentence,
                'knowledge': knowledge,
                'text': text,
                'history': history
            }
        ]
    }
    result = requests.post(url, json=request_data).json()[0]
    assert result != '', f'Got empty string as a result'
    print('Got\n{}\nSuccess'.format(result))


if __name__ == '__main__':
    test_knowledge_grounding()
