import requests


def test():
    response = requests.post('http://0.0.0.0:8120/model', json={'personality': ['Hello world']})
    assert response.status_code == 200
    assert response.json() == [[0, 1, 1, 0, 1]]
    print('SUCCESS')


if __name__ == '__main__':
    test()
