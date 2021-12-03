import logging
import os
import random
import time

from flask import Flask, request, jsonify
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

from common.fact_random import load_fact_file

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])

app = Flask(__name__)

FACTS_ANIMALS = load_fact_file("./facts_for_animals.json")
FACTS_CITIES = load_fact_file("./facts_for_cities.json")
FACTS_COUNTRIES = load_fact_file("./facts_for_countries.json")
FACTS_FOOD = load_fact_file("./food_facts.json")
ALL_FACTS = {**FACTS_ANIMALS, **FACTS_CITIES, **FACTS_COUNTRIES, **FACTS_FOOD}


def find_facts(entity_substr_list):
    facts_list = []
    for entity_substr in entity_substr_list:
        facts_for_entity = ALL_FACTS.get(entity_substr)
        if facts_for_entity:
            fact = random.choice(facts_for_entity)
            fact_data = {"entity_substr": entity_substr, "fact": fact}
            facts_list.append(fact_data)
    return facts_list


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()

    request_data = request.json
    text = request_data["text"]
    entities = request_data["entities"]

    facts = find_facts(entities)

    response = [{"text": text, "facts": facts}]

    total_time = time.time() - st_time
    logger.info(f"fact_random exec time: {total_time:.3f}s")
    return jsonify(response)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
