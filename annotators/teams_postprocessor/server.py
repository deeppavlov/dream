#!/usr/bin/env python

import logging
import re
from os import getenv
from time import time

import sentry_sdk
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
from common.skill_selector_utils_and_constants import get_available_titles_mapped_to_commands, get_all_skill_names


sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__)

# LIST
# '<ul>\r\n<li>a</li><li>b</li><li>c</li></ul>'
# '-a\n- b\n- c'
TEAMS_LIST_PATTERN = re.compile(r"<ul>(.*)</ul>", re.DOTALL)

# SUGGESTION SELECTED (&nbsp - это пробел в html)
# '<p><span>Full Report&nbsp;</span></p>'
# /full_report
TEAMS_SUGGESTION_PATTERN = re.compile(r"<p><span>(.*)</span></p>", re.DOTALL)
AVAILABLE_TITLES_TO_COMMANDS = None


def get_teams_html_content(uttr_dict):
    return uttr_dict.get("attributes", {}).get("teams_attachments", {}).get("content", "")


def process_suggestion(data, pipeline):
    """Finds command titles selected within the Suggestions mechanism in Teams.

    If any command title found in html code (Summary), returns internal command (/summary).
    If multiple internal commands correspond to command title, returns command title.
    If no command title detected, returns None.
    """
    global AVAILABLE_TITLES_TO_COMMANDS
    command = None

    if TEAMS_SUGGESTION_PATTERN.findall(data):
        soup = BeautifulSoup(data, "html.parser")
        # extract display name of the command
        command_title = [p.get_text().strip() for p in soup.find_all("span", string=True)]
        if command_title:
            # get only the first one found command
            command_title = command_title[0]
            if not AVAILABLE_TITLES_TO_COMMANDS:
                all_skill_names = get_all_skill_names({"attributes": {"pipeline": pipeline}})
                AVAILABLE_TITLES_TO_COMMANDS = get_available_titles_mapped_to_commands(all_skill_names)
            if AVAILABLE_TITLES_TO_COMMANDS:
                commands = AVAILABLE_TITLES_TO_COMMANDS.get(command_title, None)
                if commands and len(commands) > 1:
                    command = command_title
                elif commands:
                    command = commands[0]

    if command:
        return command
    else:
        return data


def process_lists(data):
    """Finds all lists formattings in the text and process html code to a texts with formatted lists
    (with long dashes)
    """
    formatted_text = ""
    list_finisher = False

    if TEAMS_LIST_PATTERN.findall(data):
        soup = BeautifulSoup(data, "html.parser")
        for element in soup.find_all():
            if element.name == "p":
                if list_finisher:
                    formatted_text += "\n"
                formatted_text += element.get_text()
            elif element.name == "ul":
                pass
            elif element.name == "li":
                formatted_text += f"\n— {element.get_text()}"
                list_finisher = True
            else:
                # TODO: not sure if there any other types acceptable, so leave it here for now
                pass

    return formatted_text.strip()


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time()
    last_human_utterances = request.json["last_human_utterances"]
    pipelines = request.json["pipelines"]
    responses = []

    try:
        for human_uttr, pipeline in zip(last_human_utterances, pipelines):
            response = human_uttr["text"]
            teams_code = get_teams_html_content(human_uttr)
            internal_command = process_suggestion(teams_code, pipeline)
            if internal_command:
                logger.info(f"Found selected command from suggestion: {internal_command}")
                response = internal_command

            processed_text = process_lists(teams_code)
            if processed_text:
                logger.info(f"Found list, formatted text: {processed_text}")
                response = processed_text
            # if command was found, return internal command as a response
            # if list were found, return formatted text
            responses.append(response)

    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
        responses = [{}] * len(last_human_utterances)

    total_time = time() - st_time
    logger.info(f"teams_postprocessor exec time: {total_time:.3f}s")
    return jsonify(responses)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
