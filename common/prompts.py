import logging
import requests

import sentry_sdk


sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

META_PROMPT = """Generate a very short description of goals of the assistant which is defined by the given prompt.

Example:
Prompt: "TASK: Your name is Life Coaching Assistant. You were made by Rhoades & Co. Help the human set a goal in their life and determine how to achieve them step by step. Do not discuss other topics. Respond with empathy. Ask open-ended questions to help the human understand themselves better.\nINSTRUCTION: A human enters the conversation. Introduce yourself concisely. Help them set a goal and achieve it. You can ask about their life priorities and preferable areas of concentration and suggest useful ideas. You must ask ONE question or NO questions, NOT two or three. Stop after you ask the first question."
Result: Helps user to establish and achieve life goals.
"""


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
    except Exception as e:
        goals_description = prompt
    return goals_description
