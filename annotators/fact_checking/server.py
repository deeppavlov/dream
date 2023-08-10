import logging
from os import getenv
import sentry_sdk
import json
from flask import Flask, jsonify, request
from sentry_sdk.integrations.flask import FlaskIntegration
from common.prompts import send_request_to_prompted_generative_service, compose_sending_variables

# logging here because it conflicts with tf

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
sentry_sdk.init(dsn=getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])
app = Flask(__name__)

EXTERNAL_SKILLS = ["factoid_qa", "dff_google_api_skill"]
ENVVARS_TO_SEND = getenv("ENVVARS_TO_SEND", None)
ENVVARS_TO_SEND = [] if ENVVARS_TO_SEND is None else ENVVARS_TO_SEND.split(",")
GENERATIVE_SERVICE_URL = getenv("GENERATIVE_SERVICE_URL")
GENERATIVE_TIMEOUT = int(getenv("GENERATIVE_TIMEOUT", 0))
GENERATIVE_SERVICE_CONFIG = getenv("GENERATIVE_SERVICE_CONFIG")
if GENERATIVE_SERVICE_CONFIG:
    with open(f"common/generative_configs/{GENERATIVE_SERVICE_CONFIG}", "r") as f:
        GENERATIVE_SERVICE_CONFIG = json.load(f)


@app.route("/respond", methods=["POST"])
def respond():
    hypotheses = request.json["hypotheses"]
    human_uttr_attributes = request.json["human_uttr_attributes"] # CHECK HOW 2 GET
    external_service_hyps = [hyp["text"] for hyp in hypotheses if hyp["skill_name"] in EXTERNAL_SKILLS] # considered correct (always)
    internal_service_hyps = [hyp["text"] for hyp in hypotheses if hyp["skill_name"] not in EXTERNAL_SKILLS] # need to be checked
    try:
        results = []
        if len(external_service_hyps) == 0:
            if len(internal_service_hyps) > 0:
                logger.info(f"No external hypotheses to be used as ground truth. Marking all internal hypotheses as correct.")
                results += ['Correct']*len(internal_service_hyps) # add always correct
            else:
                logger.info(f"No hypotheses provided.")
        else:
            logger.info(f"Checking whether internal hypotheses contradict to any of the external hypotheses.")
            for external_hyp in external_service_hyps:
                results += ['Correct'] * len(external_service_hyps)
            if len(internal_service_hyps) > 0:    
                for internal_hyp in internal_service_hyps:
                    is_hyp_correct = True
                    for external_hyp in external_service_hyps:
                        curr_prompt = f'''Fact:{external_hyp} 
Hypothesis: {internal_hyp}
Does Hypothesis contain any information that contradicts Fact? Always answer only Yes or No.'''
                        logger.info(f"Sending prompt to llm to fact-check:\n`{curr_prompt}`")
                        lm_service_kwargs = human_uttr_attributes.pop("lm_service_kwargs", None)
                        lm_service_kwargs = {} if lm_service_kwargs is None else lm_service_kwargs
                        envvars_to_send = ENVVARS_TO_SEND if len(ENVVARS_TO_SEND) else human_uttr_attributes.get("envvars_to_send", [])
                        sending_variables = compose_sending_variables(
                            lm_service_kwargs,
                            envvars_to_send,
                            **human_uttr_attributes,
                        )
                        response = send_request_to_prompted_generative_service(
                            "", # нужен ли нам контекст и какой длины?
                            curr_prompt,
                            GENERATIVE_SERVICE_URL,
                            GENERATIVE_SERVICE_CONFIG,
                            GENERATIVE_TIMEOUT,
                            sending_variables,
                        )
                        result = response[0]
                        logger.info(f"llm response: `{result}`")
                        if 'no' in result.lower():
                            is_hyp_correct = False
                    if is_hyp_correct:
                        results += ["Correct"]
                    else:
                        results += ["Incorrect"]
    except Exception as e:
        logger.error(e)
        results.append(["Correct"] * len(hypotheses))
    return jsonify([{"batch": results}])

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
