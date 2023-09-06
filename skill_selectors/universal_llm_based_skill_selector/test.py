import requests
from os import getenv


SERVICE_PORT = int(getenv("SERVICE_PORT"))


def test_respond():
    result = requests.post(
        f"http://0.0.0.0:{SERVICE_PORT}/respond",
        json={
            "dialogs": [
                {
                    "attributes": {
                        "pipeline": [
                            "skills.dummy_skill",
                            "skills.dff_official_email_prompted_skill",
                            "skills.dff_plan_for_article_prompted_skill",
                        ],
                    },
                    "human_utterances": [
                        {
                            "text": "help me with my article about penguins",
                        }
                    ],
                    "utterances": [
                        {
                            "text": "help me with my article about penguins",
                        }
                    ],
                }
            ],
        },
    ).json()[0]
    print(result)

    assert "dff_plan_for_article_prompted_skill" in result, f"Got\n{result}\n, something is wrong"
    print("Success!")


if __name__ == "__main__":
    test_respond()
