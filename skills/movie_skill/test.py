import requests
import json


def get_input_json(fname):
    with open(fname, "r") as f:
        res = json.load(f)
    return {"dialogs": [res]}


def test_one_step_responses():
    url = 'http://0.0.0.0:8023/movie_skill'

    print("check_actor")
    input_data = get_input_json("test_configs/check_actor.json")
    response = requests.post(url, json=input_data).json()[0]
    assert "Chris Evans" in response[0], print(response)

    print("check_director_more_important_than_actor")
    input_data = get_input_json("test_configs/check_director_more_important_than_actor.json")
    response = requests.post(url, json=input_data).json()[0]
    assert 'Steven Spielberg' in response[0], print(response)

    print("check_movie")
    input_data = get_input_json("test_configs/check_movie.json")
    response = requests.post(url, json=input_data).json()[0]
    assert 'The Avengers' in response[0] and response[1] == 1., print(response)

    print("check_persons_comparison")
    input_data = get_input_json("test_configs/check_persons_comparison.json")
    response = requests.post(url, json=input_data).json()[0]
    assert response[1:] == [1.0, {}, {}, {}], print(response)

    print("check_persons_comparison2")
    input_data = get_input_json("test_configs/check_persons_comparison2.json")
    response = requests.post(url, json=input_data).json()[0]
    assert "Brad Pitt" in response[0], print(response)

    print("check_genre")
    input_data = get_input_json("test_configs/check_genre.json")
    response = requests.post(url, json=input_data).json()[0]
    assert "comedies" in response[0], print(response)

    print("check_favorite_genres")
    input_data = get_input_json("test_configs/check_favorite_genres.json")
    response = requests.post(url, json=input_data).json()[0]
    assert "science fiction and documentary" in response[0], print(response)
    #
    # print("check_get_opinion_give_opinion")
    # input_data = get_input_json("test_configs/check_get_opinion_give_opinion.json")
    # response = requests.post(url, json=input_data).json()[0]
    # assert response[1:] == [0.9, {}, {}, {'bot_attitudes': [['Comedy', 'genre', 'very_positive']],
    #                                       'human_attitudes': []}], \
    #     print(response)

    print("check_ignored_movie")
    input_data = get_input_json("test_configs/check_ignored_movie.json")
    response = requests.post(url, json=input_data).json()[0]
    assert response[2]['discussed_movie_titles'] == ['Her'], print(response)

    print("check_favorite_movie")
    input_data = get_input_json("test_configs/check_favorite_movie.json")
    response = requests.post(url, json=input_data).json()[0]
    assert "Star Wars" in response[0], print(response)

    print("check_less_favorite_movie")
    input_data = get_input_json("test_configs/check_less_favorite_movie.json")
    response = requests.post(url, json=input_data).json()[0]
    assert "I don't like musicals" in response[0], print(response)

    print("check_favorite_genre")
    input_data = get_input_json("test_configs/check_favorite_genre.json")
    response = requests.post(url, json=input_data).json()[0]
    assert "comedies" in response[0], print(response)

    print("check_less_favorite_genre")
    input_data = get_input_json("test_configs/check_less_favorite_genre.json")
    response = requests.post(url, json=input_data).json()[0]
    assert "film-noir, mysteries and musicals" in response[0], print(response)

    print("check_favorite_actor")
    input_data = get_input_json("test_configs/check_favorite_actor.json")
    response = requests.post(url, json=input_data).json()[0]
    assert "Brad Pitt" in response[0], print(response)

    print("check_favorite_actress")
    input_data = get_input_json("test_configs/check_favorite_actress.json")
    response = requests.post(url, json=input_data).json()[0]
    assert "Jodie Foster" in response[0], print(response)

    print("SUCCESS!")


if __name__ == '__main__':
    test_one_step_responses()
