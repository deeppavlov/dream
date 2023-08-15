import logging
from os import getenv
import sentry_sdk
import json
from flask import Flask, jsonify, request
from sentry_sdk.integrations.flask import FlaskIntegration
from common.prompts import send_request_to_prompted_generative_service, compose_sending_variables
from common.response_selection import EXTERNAL_SKILLS

# logging here because it conflicts with tf

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
sentry_sdk.init(dsn=getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])
app = Flask(__name__)

ENVVARS_TO_SEND = getenv("ENVVARS_TO_SEND", None)
ENVVARS_TO_SEND = [] if ENVVARS_TO_SEND is None else ENVVARS_TO_SEND.split(",")
GENERATIVE_SERVICE_URL = getenv("GENERATIVE_SERVICE_URL")
GENERATIVE_TIMEOUT = int(getenv("GENERATIVE_TIMEOUT"))
GENERATIVE_SERVICE_CONFIG = getenv("GENERATIVE_SERVICE_CONFIG")
if GENERATIVE_SERVICE_CONFIG:
    with open(f"common/generative_configs/{GENERATIVE_SERVICE_CONFIG}", "r") as f:
        GENERATIVE_SERVICE_CONFIG = json.load(f)
SKILLS_NOT_TO_FACT_CHECK = ["dummy_skill", "dff_intent_responder_skill"]


def check_hyp_with_llm(curr_prompt, human_uttr_attr):
    lm_service_kwargs = human_uttr_attr.pop("lm_service_kwargs", None)
    lm_service_kwargs = {} if lm_service_kwargs is None else lm_service_kwargs
    envvars_to_send = ENVVARS_TO_SEND if len(ENVVARS_TO_SEND) else human_uttr_attr.get("envvars_to_send", [])
    sending_variables = compose_sending_variables(
        lm_service_kwargs,
        envvars_to_send,
        **human_uttr_attr,
    )
    response = send_request_to_prompted_generative_service(
        "",
        curr_prompt,
        GENERATIVE_SERVICE_URL,
        GENERATIVE_SERVICE_CONFIG,
        GENERATIVE_TIMEOUT,
        sending_variables,
    )
    result = response[0]
    if "yes" in result.lower():
        _is_hyp_correct = False
    else:
        _is_hyp_correct = True
    return _is_hyp_correct


@app.route("/respond_batch", methods=["POST"])
def respond_batch():
    hypotheses = request.json["hypotheses"]
    human_uttr_attributes = request.json["human_uttr_attributes"]
    ie_types = ["external" if hyp["skill_name"] in EXTERNAL_SKILLS else "internal" for hyp in hypotheses]
    external_service_hyps = [
        (hyp["text"], hyp["skill_name"]) for hyp in hypotheses if hyp["skill_name"] in EXTERNAL_SKILLS
    ]
    results = []
    for hyp, human_uttr_attr, ie_type in zip(hypotheses, human_uttr_attributes, ie_types):
        hyp_text = hyp["text"]
        try:
            if ie_type == "external":
                logger.info(f"Hypothesis `{hyp_text}` is considered correct as it is external.")
                results += ["Correct"]
            elif hyp["skill_name"] in SKILLS_NOT_TO_FACT_CHECK:
                logger.info(f"Hypothesis `{hyp_text}` is not checked as it was produced by {hyp['skill_name']}.")
                results += ["Correct"]
            else:
                if len(external_service_hyps) == 0:
                    logger.info(
                        f"Internal hypothesis `{hyp_text}` is considered correct as there are no external hypotheses \
to check it upon."
                    )
                    results += ["Correct"]
                else:
                    _is_hyp_correct = True
                    for external_service_hyp, external_service_name in external_service_hyps:
                        curr_prompt = f"""Hypothesis: "{hyp_text}"
Does Hypothesis contradict Fact that {external_service_hyp}? Always answer only Yes or No without explanation."""
                        logger.info(f"Checking internal hypothesis `{hyp_text}` with LLM. Prompt: {curr_prompt}")
                        _is_hyp_correct_one_step = check_hyp_with_llm(curr_prompt, human_uttr_attr)
                        if not _is_hyp_correct_one_step:
                            _is_hyp_correct = False
                            logger.info(
                                f"""Internal hypothesis `{hyp_text}` is incorrect according to external service \
{external_service_name}."""
                            )
                            results += ["Incorrect"]
                            break
                    if _is_hyp_correct:
                        logger.info(f"Internal hypothesis `{hyp_text}` is correct according to all external services.")
                        results += ["Correct"]
        except Exception as e:
            logger.error(e)
            results += ["Correct"]
    return jsonify([{"batch": results}])


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
