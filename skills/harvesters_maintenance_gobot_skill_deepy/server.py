import logging
import time
import random
import json

from flask import Flask, request, jsonify

from deeppavlov import build_model
from deeppavlov.core.common.file import read_yaml, read_json


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


class GoBotWrapper:
    def __init__(self, gobot_config_path):
        gobot_config = read_json(f"{gobot_config_path}/gobot_config.json")
        domain_yml_path = "dp_minimal_demo_dir/domain.yml"

        self.response_templates = read_yaml(domain_yml_path)["responses"]
        self.gobot = build_model(gobot_config)

        self.DATABASE, self.PREV_UPDATE_TIME = self._update_database()

    def __call__(self, sentence):
        gobot_response = self.gobot([sentence])[0][0]

        uttr_response_action = gobot_response.actions_tuple
        confidence = gobot_response.policy_prediction.probs[gobot_response.policy_prediction.predicted_action_ix]

        confidence = confidence.astype(float)
        uttr_slots = self.gobot.pipe[-1][-1].nlu_manager.nlu(sentence).slots
        return {"act": uttr_response_action, "slots": uttr_slots}, confidence

    def getNlg(self, gobot_response):
        act = gobot_response["act"][0]
        slots = gobot_response["slots"]
        response_template = self.response_templates.get(act, [{"text": ""}])[0]["text"]

        generated = self._generate_response_from_storage(response_template, slots)

        return generated

    def reset(self):
        self.gobot.reset()
        self("start")

    # region storage interaction logic
    def _update_database(self):
        """Update database loading new version every our"""
        with open("harvesters_status.json", "r") as f:
            db = json.load(f)
        return db, time.time()

    def _get_ids_with_statuses(self, status, object="harvester"):
        """Return ids of objects with given (inner) status"""
        if len(status) == 0:
            return []
        if object == "harvester":
            status_map = {
                "working": ["optimal", "suboptimal"],
                "full": ["full"],
                "stall": ["stall"],
                "inactive": ["inactive"],
            }
            statuses = status_map[status]
        else:
            statuses = [status]

        ids = []
        for str_id in self.DATABASE[f"{object}s"]:
            if self.DATABASE[f"{object}s"][str_id] in statuses:
                ids.append(str_id)
        return ids

    def _get_statuses_with_ids(self, ids, object="harvester"):
        """Return (inner) statuses of objects with given ids"""
        # harvesters statuses are out of ["full", "working", "stall", "inactive"]
        if object == "harvester":
            status_map = {
                "optimal": "working",
                "suboptimal": "working",
                "full": "full",
                "stall": "stall",
                "inactive": "inactive",
            }
        else:
            status_map = {"available": "available", "stall": "stall", "inactive": "inactive"}

        statuses = []
        for str_id in ids:
            statuses.append(status_map[self.DATABASE[f"{object}s"][str_id]])
        return statuses

    def _fill_in_particular_status(self, response, ids, template_to_fill, object="harvester"):
        """Replaces `template_to_fill` (e.g. `full_ids`) in templated response to objects with given `ids`"""
        template_to_fill = "{" + template_to_fill + "}"
        if len(ids) == 0:
            response = response.replace(f"{object} {template_to_fill} is", "none is")
        elif len(ids) == 1:
            response = response.replace(f"{template_to_fill}", str(ids[0]))
        else:
            response = response.replace(f"{object} {template_to_fill} is", f"{object}s {', '.join(ids)} are")
        return response

    def _fill_harvesters_status_templates(self, response, slots):
        """Fill all variables in the templated response"""
        full_ids = self._get_ids_with_statuses("full")
        working_ids = self._get_ids_with_statuses("working")
        broken_ids = self._get_ids_with_statuses("stall")
        inactive_ids = self._get_ids_with_statuses("inactive")

        available_rovers_ids = self._get_ids_with_statuses("available", object="rover")
        inactive_rovers_ids = self._get_ids_with_statuses("inactive", object="rover")
        broken_rovers_ids = self._get_ids_with_statuses("stall", object="rover")

        response = response.replace("total_harvesters_number", str(len(self.DATABASE["harvesters"])))

        response = self._fill_in_particular_status(response, full_ids, "full_ids", "harvester")
        response = self._fill_in_particular_status(response, working_ids, "working_ids", "harvester")
        response = self._fill_in_particular_status(response, broken_ids, "broken_ids", "harvester")
        response = self._fill_in_particular_status(response, inactive_ids, "inactive_ids", "harvester")

        response = self._fill_in_particular_status(response, available_rovers_ids, "available_rover_ids", "rover")
        response = self._fill_in_particular_status(response, inactive_rovers_ids, "inactive_rover_ids", "rover")
        response = self._fill_in_particular_status(response, broken_rovers_ids, "broken_rover_ids", "rover")

        if len(available_rovers_ids) == 1:
            avail_rover_id = available_rovers_ids[0]
        elif len(available_rovers_ids) > 1:
            avail_rover_id = random.choice(available_rovers_ids)
        response = response.replace("rover_for_trip_id", f"{avail_rover_id}")

        logger.info(f"slots: {slots}")
        print("slots: ", slots, flush=True)
        if "_id" in response:
            # re.search(r"[0-9]+", request_text)
            required_id = slots.get("number")
            print(required_id)
            if required_id is not None:
                required_id = required_id[0]
            if required_id is not None and required_id in self.DATABASE["harvesters"]:
                status = self._get_statuses_with_ids([required_id])[0]
                response = response.replace("harvester_id", required_id)
                response = response.replace("harvester_status", status)
            else:
                response = (
                    f"I can answer only about the following harvesters ids: "
                    f"{', '.join(self.DATABASE['harvesters'].keys())}."
                )

        response = response.replace("{", "").replace("}", "")
        return response

    def _generate_response_from_storage(self, response, slots):
        if time.time() - self.PREV_UPDATE_TIME >= 3600:
            self.DATABASE, self.PREV_UPDATE_TIME = self._update_database()

        response = self._fill_harvesters_status_templates(response, slots)

        return response

    # endregion storage interaction logic


gobot = GoBotWrapper("dp_minimal_demo_dir")


@app.route("/reset", methods=["GET"])
def reset():
    logger.info("resetting the gobot")
    gobot.reset()
    return ("", 204)


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()

    dialogs = request.json["dialogs"]

    responses = []
    confidences = []

    for dialog in dialogs:
        sentence = dialog["human_utterances"][-1]["annotations"].get("spelling_preprocessing")

        if sentence is None:
            logger.warning("Not found spelling preprocessing annotation")
            sentence = dialog["human_utterances"][-1]["text"]

        uttr_resp, conf = gobot(sentence)
        response = gobot.getNlg(uttr_resp)

        responses.append(response)
        confidences.append(conf)

    total_time = time.time() - st_time
    logger.info(f"harvesters_maintenance_gobot_skill exec time = {total_time:.3f}s")
    return jsonify(list(zip(responses, confidences)))


if __name__ == "__main__":
    reset()
    app.run(debug=False, host="0.0.0.0", port=3000)
