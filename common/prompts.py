import json
import logging
import requests
from copy import deepcopy
from os import getenv


logger = logging.getLogger(__name__)

with open("common/prompts/goals_for_prompts.json", "r") as f:
    META_GOALS_PROMPT = json.load(f)["prompt"]


def send_request_to_prompted_generative_service(dialog_context, prompt, url, config, timeout, sending_variables):
    response = requests.post(
        url,
        json={
            "dialog_contexts": [dialog_context],
            "prompts": [prompt],
            "configs": [config],
            **sending_variables,
        },
        timeout=timeout,
    )
    hypotheses = response.json()[0]
    return hypotheses


def get_goals_from_prompt(prompt, url, generative_timeout, sending_variables):
    new_url = "/".join(url.split("/")[:-1])
    try:
        goals_description = requests.post(
            f"{new_url}/generate_goals",
            json={
                "prompts": [prompt],
                **sending_variables,
            },
            timeout=generative_timeout,
        ).json()[0]
    except Exception as e:
        logger.info(f"Exception in `/generate_goals` endpoint:\n{e}")
        goals_description = prompt
    return goals_description


def if_none_var_values(sending_variables):
    if len(sending_variables) > 0 and all(
        [var_value[0] is None or var_value[0] == "" for var_value in sending_variables.values()]
    ):
        return True
    return False


def compose_sending_variables(lm_service_kwargs, envvars_to_send, **kwargs):
    if len(envvars_to_send):
        # get variables which names are in `envvars_to_send` (splitted by comma if many)
        # from the last human utterance's attributes
        sending_variables = {f"{var.lower()}s": [kwargs.get(var.lower(), None)] for var in envvars_to_send}
        if if_none_var_values(sending_variables):
            # get variables which names are in `envvars_to_send` (splitted by comma if many)
            # from env variables
            sending_variables = {f"{var.lower()}s": [getenv(var, None)] for var in envvars_to_send}
            if if_none_var_values(sending_variables):
                logger.info(f"Did not get {envvars_to_send}'s values. Sending without them.")
            else:
                logger.info(f"Got {envvars_to_send}'s values from environment.")
        else:
            logger.info(f"Got {envvars_to_send}'s values from attributes.")
    else:
        sending_variables = {}

    # adding kwargs to request from the last human utterance's attributes
    for _key, _value in lm_service_kwargs.items():
        logger.info(f"Got/Re-writing {_key}s values from kwargs.")
        sending_variables[f"{_key}s"] = [deepcopy(_value)]
    return sending_variables
