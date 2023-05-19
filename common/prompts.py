import json
import requests


with open("prompts/goals_for_prompts.json", "r") as f:
    META_PROMPT = json.load(f)["prompt"]


def send_request_to_prompted_generative_service(dialog_context, prompt, url, config, timeout, sending_variables):
    response = requests.post(
        url,
        json={
            "dialog_contexts": [dialog_context],
            "prompts": prompt,
            "configs": [config],
            **sending_variables,
        },
        timeout=timeout,
    )
    hypotheses = response.json()[0]
    return hypotheses


def get_goals_from_prompt(prompt, url, config, generative_timeout, sending_variables):
    context = ["hi", META_PROMPT + f'Prompt: "{prompt}"\nResult:']
    try:
        result = send_request_to_prompted_generative_service(
            context,
            prompt="",
            url=url,
            config=config,
            timeout=generative_timeout,
            sending_variables=sending_variables,
        )
        goals_description = result[0]
    except Exception:
        goals_description = prompt
    return goals_description
