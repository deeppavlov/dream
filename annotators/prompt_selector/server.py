import json
import logging
import re
import requests
import time
from copy import deepcopy
from os import getenv, listdir
from pathlib import Path

import numpy as np
import sentry_sdk
from flask import Flask, request, jsonify

from common.prompts import send_request_to_prompted_generative_service, compose_sending_variables


sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)
app = Flask(__name__)

SENTENCE_RANKER_SERVICE_URL = getenv("SENTENCE_RANKER_SERVICE_URL")
logger.info(f"prompt-selector considered ranker: {SENTENCE_RANKER_SERVICE_URL}")
N_SENTENCES_TO_RETURN = int(getenv("N_SENTENCES_TO_RETURN"))
# list of string names of prompts from common/prompts
PROMPTS_TO_CONSIDER = getenv("PROMPTS_TO_CONSIDER", "").split(",")
logger.info(f"prompt-selector considered prompts: {PROMPTS_TO_CONSIDER}")
PROMPTS = []
PROMPTS_NAMES = []
for filename in listdir("common/prompts"):
    prompt_name = Path(filename).stem
    if ".json" in filename and prompt_name in PROMPTS_TO_CONSIDER:
        data = json.load(open(f"common/prompts/{filename}", "r"))
        PROMPTS.append(data.get("goals", ""))
        PROMPTS_NAMES.append(prompt_name)

GENERATIVE_TIMEOUT = int(getenv("GENERATIVE_TIMEOUT", 5))
GENERATIVE_SERVICE_URL = getenv("GENERATIVE_SERVICE_URL")
GENERATIVE_SERVICE_CONFIG = getenv("GENERATIVE_SERVICE_CONFIG")
if GENERATIVE_SERVICE_CONFIG:
    with open(f"generative_configs/{GENERATIVE_SERVICE_CONFIG}", "r") as f:
        GENERATIVE_SERVICE_CONFIG = json.load(f)
ENVVARS_TO_SEND = getenv("ENVVARS_TO_SEND", None)
ENVVARS_TO_SEND = [] if ENVVARS_TO_SEND is None else ENVVARS_TO_SEND.split(",")

SKILL_SELECTION_PROMPT = json.load(open(f"common/prompts/skill_selector.json", "r"))["prompt"]
SKILL_SELECTION_PROMPT = SKILL_SELECTION_PROMPT.replace("N_SENTENCES_TO_RETURN", str(N_SENTENCES_TO_RETURN))
skill_names_compiled = re.compile(r'"([A-Z0-9a-z_]+)"')


def cut_context(context, return_str=True):
    if len(context[-1].split()) < 5:
        depth = 3
    else:
        depth = 1

    if return_str:
        return "\n".join(context[-depth:])
    else:
        return context[-depth:]


def select_with_sentence_ranker(contexts, pairs, context_ids, is_empty_prompts):
    result = []

    scores = requests.post(SENTENCE_RANKER_SERVICE_URL, json={"sentence_pairs": pairs}, timeout=1.5).json()[0][
        "batch"
    ]
    scores = np.array(scores)
    for i, context in enumerate(contexts):
        curr_ids = np.where(context_ids == i)[0]
        # assign to -1 scores for pairs with empty prompt (actually, its goals)
        for _id in curr_ids:
            if is_empty_prompts[_id]:
                scores[_id] = -1.0
        most_relevant_sent_ids = np.argsort(scores[curr_ids])[::-1][:N_SENTENCES_TO_RETURN]
        curr_result = {
            "prompts": [PROMPTS_NAMES[_id] for _id in most_relevant_sent_ids],
            "max_similarity": scores[curr_ids][most_relevant_sent_ids[0]],
        }
        # add to prompts to be turned on, those prompts which goals are empty
        for _id in curr_ids:
            if is_empty_prompts[_id]:
                curr_result["prompts"] += [PROMPTS_NAMES[_id]]
        result += [curr_result]
    return result


def select_with_generative_service(contexts, human_uttr_attributes):
    result = []

    for context, uttr_attrs in zip(contexts, human_uttr_attributes):
        lm_service_kwargs = uttr_attrs.pop("lm_service_kwargs", None)
        lm_service_kwargs = {} if lm_service_kwargs is None else lm_service_kwargs
        envvars_to_send = ENVVARS_TO_SEND if len(ENVVARS_TO_SEND) else uttr_attrs.get("envvars_to_send", [])
        sending_variables = compose_sending_variables(
            lm_service_kwargs,
            envvars_to_send,
            **uttr_attrs,
        )
        dialog_context = "\n".join([f'"{el}"' for el in cut_context(context, return_str=False)])
        dialog_context = f'Dialog context:\n\n{dialog_context}'

        skills_descriptions = "\n".join([f'"{pname}": "{pdescr}"' for pname, pdescr in zip(PROMPTS_NAMES, PROMPTS)])
        skills_descriptions = f'Names and Descriptions of Skills:\n\n{skills_descriptions}'

        resp = send_request_to_prompted_generative_service(
            [f"{dialog_context}\n\n{skills_descriptions}\n"],
            SKILL_SELECTION_PROMPT,
            GENERATIVE_SERVICE_URL,
            GENERATIVE_SERVICE_CONFIG,
            GENERATIVE_TIMEOUT,
            sending_variables)[0][0]
        result += [skill_names_compiled.findall(resp)]
    return result


def get_result(request):
    global PROMPTS, PROMPTS_NAMES
    st_time = time.time()
    # batch of contexts
    contexts = request.json["contexts"]
    # batch of prompts_goals dicts [{"promptname1": "promptgoal1", "promptname2": "promptgoal2"}]
    prompts_goals_from_attributes = request.json["prompts_goals"]
    last_human_utterances = request.json["last_human_utterances"]

    pairs = []
    context_ids = []

    for context_id, context in enumerate(contexts):
        str_context = cut_context(context)
        for _prompt_goals, _prompt_name in zip(PROMPTS, PROMPTS_NAMES):
            pairs += [
                [
                    str_context,
                    prompts_goals_from_attributes[context_id].get(_prompt_name, "")
                    if not _prompt_goals
                    else _prompt_goals,
                ]
            ]
            context_ids += [context_id]
    context_ids = np.array(context_ids)
    is_empty_prompts = np.array([len(pair[1]) == 0 for pair in pairs])
    if all(is_empty_prompts):
        logger.info("All goals from prompts are empty. Skip ranking.")
        result = [{"prompts": [], "max_similarity": 0.0}] * len(contexts)
    else:
        try:
            if GENERATIVE_SERVICE_URL:
                human_uttr_attributes = [uttr.get("attributes", {}) for uttr in last_human_utterances]
                result = select_with_generative_service(contexts, human_uttr_attributes)
            else:
                result = select_with_sentence_ranker(contexts, pairs, context_ids, is_empty_prompts)
        except Exception as exc:
            logger.exception(exc)
            sentry_sdk.capture_exception(exc)
            result = [{"prompts": [], "max_similarity": 0.0}] * len(contexts)

    total_time = time.time() - st_time
    logger.info(f"prompt-selector exec time: {total_time:.3f}s")
    logger.info(f"prompt-selector result: {result}")
    return result


@app.route("/collect_goals", methods=["POST"])
def collect_goals():
    # prompts_goals_from_attributes = [{"promptname1": "promptgoal1", "promptname2": "promptgoal2"}]
    # these are goals from attributes of skills' hypotheses, generated by LLMs on the previous step of the dialog
    prompts_goals_from_attributes = request.json["prompts_goals"]
    # these are human attributes which may already contain goals for some prompts
    human_attributes = request.json["human_attributes"]
    result = []

    for _prompts_goals_all, _human_attr in zip(prompts_goals_from_attributes, human_attributes):
        # _prompts_goals_all = {"promptname1": "promptgoal1", "promptname2": "promptgoal2"}
        _prompts_goals_not_empty = {name: goals for name, goals in _prompts_goals_all.items() if len(goals)}
        _new_prompts_goals = deepcopy(_human_attr.get("prompts_goals", {}))
        _new_prompts_goals.update(_prompts_goals_not_empty)
        result += [{"human_attributes": {"prompts_goals": _new_prompts_goals}}]
    logger.info(f"prompt_selector collected goals from hypotheses' attributes: {result}")
    return jsonify(result)


@app.route("/respond", methods=["POST"])
def respond():
    result = get_result(request)
    return jsonify(result)


@app.route("/respond_batch", methods=["POST"])
def respond_batch():
    result = get_result(request)
    return jsonify([{"batch": result}])


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
