import common.link as link


def test_link_to():
    link_result = link.link_to(['news_api_skill'], {})
    assert link_result['phrase']
    assert link_result['skill']

    link_result = link.link_to(['news_api_skill', 'dff_movie_skill', 'book_skill'], {})
    print(link_result)


if __name__ == "__main__":
    test_link_to()
