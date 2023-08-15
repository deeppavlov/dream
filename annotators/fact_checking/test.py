import requests


def main():
    url = "http://0.0.0.0:8182/respond"
    result = requests.post(
        url=url,
        json={
            "hypotheses": [
                {"skill_name": "dff_google_api_skill", "text": "Jack is 5 years old."},
                {
                    "skill_name": "dff_dream_persona_chatgpt_prompted_skill",
                    "text": "Jack is 25 years old.",
                },
                {
                    "skill_name": "dummy_skill",
                    "text": "Sorry, I cannot answer your question.",
                },
            ],
            "human_uttr_attributes": [{}, {}, {}],
        },
    )
    result = result.json()[0]["batch"]
    result_gold = ["Correct", "Incorrect", "Correct"]
    assert result == result_gold, f"Got\n{result}\n, something is wrong"
    print("Success!")


if __name__ == "__main__":
    main()
