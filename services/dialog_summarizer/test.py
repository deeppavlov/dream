import requests


def test_skill():
    url = "http://0.0.0.0:8059/respond_batch"

    input_data = {
        "sentences": [
            "Generative pre-trained transformers (GPT) are a family of large language models (LLMs)"
            ", which was introduced in 2018 by the American artificial intelligence organization "
            "OpenAI. GPT models are artificial neural networks that are based on the transformer "
            "architecture, pre-trained on large datasets of unlabelled text, and able to generate "
            "novel human-like text. At this point, most LLMs have these characteristics.",
            "ChatGPT is an artificial-intelligence (AI) chatbot developed by OpenAI and launched "
            "in November 2022. It is built on top of OpenAI's GPT-3.5 and GPT-4 families of large "
            "language models (LLMs) and has been fine-tuned (an approach to transfer learning) "
            "using both supervised and reinforcement learning techniques. The original release of "
            "ChatGPT was based on GPT-3.5. A version based on GPT-4, the newest OpenAI model, was "
            "released on March 14, 2023, and is available for paid subscribers on a limited basis.",
        ]
    }
    desired_output = [
        "Generative pre-trained transformers are a family of large language models (LLMs) introduced by "
        "the American artificial intelligence organization OpenAI.",
        "ChatGPT is an artificial-intelligence chatbot developed by OpenAI. It was launched in November "
        "2022. A version based on GPT-4 model was released on March 14, 2023 and is available for paid "
        "subscribers.",
    ]

    result = requests.post(url, json=input_data).json()[0]["batch"]

    assert result == desired_output
    print("SUCCESS!")


if __name__ == "__main__":
    test_skill()
