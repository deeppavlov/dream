import requests


def test_question_generator():
    url = "http://0.0.0.0:8079/question"

    text = (
        "Lipa was born on 22 August 1995 in London to Kosovar Albanian parents who had moved from Pristina, "
        "FR Yugoslavia in 1992. Her father—Dukagjin Lipa—is a marketing manager and the lead vocalist in the "
        "Kosovan rock band Oda, while her mother—Anesa Lipa (née Rexha)—works in tourism. Through her maternal "
        "grandmother, Lipa is also of Bosnian descent."
    )
    answer = "a marketing manager"

    request_data = {"text": text, "answer": answer}

    result = requests.post(url, json=request_data).json()

    gold_result = {"question": "What is Lipa's father's job?"}

    assert result == gold_result, f"Got\n{result}\n, but expected:\n{gold_result}"
    print("Success")


if __name__ == "__main__":
    test_question_generator()
