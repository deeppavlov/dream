import logging
import os
import sentry_sdk
from flask import Flask, jsonify, request
from sentry_sdk.integrations.flask import FlaskIntegration
from utils import upload_documents_save_info
from common.files_and_folders_processing import SKILLS_USING_DOC

# logging here because it conflicts with tf

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"), integrations=[FlaskIntegration()])
app = Flask(__name__)

DOC_PATHS_OR_LINKS = os.environ.get("DOC_PATHS_OR_LINKS")
if DOC_PATHS_OR_LINKS:
    DOC_PATHS_OR_LINKS = DOC_PATHS_OR_LINKS.split(",")  # we may have multiple files
else:
    DOC_PATHS_OR_LINKS = []
FILE_SERVER_URL = os.environ.get("FILE_SERVER_URL")
assert FILE_SERVER_URL, logger.error("Error: FILE_SERVER_URL is not specified in env")
N_TURNS_TO_KEEP_DOC = os.environ.get("N_TURNS_TO_KEEP_DOC")
if N_TURNS_TO_KEEP_DOC:
    N_TURNS_TO_KEEP_DOC = int(N_TURNS_TO_KEEP_DOC)


@app.route("/process_and_upload_doc", methods=["POST"])
def process_and_upload_doc():
    attributes_to_add = []
    dialogs = request.json["dialogs"]
    all_prev_active_skills = request.json["all_prev_active_skills"]
    for n, dialog in enumerate(dialogs):
        try:
            human_atts = {}
            dialog_id = dialog["dialog_id"]
            human_utts = dialog.get("human_utterances", [{}])
            bot_utts = dialog.get("bot_utterances", [])
            docs_in_atts = human_utts[-1].get("attributes", {}).get("documents", [])
            all_docs_info = dialog.get("human", {}).get("attributes", {}).get("processed_documents", {})
            docs_combination_ids_info = (
                dialog.get("human", {}).get("attributes", {}).get("documents_combination_ids", {})
            )
            docs_in_use_info = dialog.get("human", {}).get("attributes", {}).get("documents_in_use", [])
            # even if we reset the dialog, we may still get some old files in docs_in_use
            # thus, for a new dialog, we manually reset docs_in_use
            if len(human_utts) == 1 and len(bot_utts) == 0:
                docs_in_use_info = []
            # check if we got sth from attributes (docs_in_atts) or arguments (DOC_PATHS_OR_LINKS)
            # if these docs were not processed yet, process them and upload to file server
            # if these docs were already processed, just reset n_steps_discussed
            new_docs_in_use_info, new_docs_info, docs_combination_ids_new = upload_documents_save_info(
                docs_in_atts, DOC_PATHS_OR_LINKS, all_docs_info, docs_in_use_info, dialog_id
            )
            # update dicts to be used in human_attributes with new info for docs_in_use
            # and new combination id for these new docs_in_use
            # if we got new docs, remove the old ones from docs_in_use_info
            if new_docs_in_use_info:
                docs_in_use_info = new_docs_in_use_info
                docs_combination_ids_info.update(docs_combination_ids_new)
            # only update attributes if we received some documents
            if new_docs_info:
                all_docs_info.update(new_docs_info)
                logger.info("Received and processed new document(s).")
            # if no new documents received, we can either leave the attributes as they are
            # or in some cases clear active documents if we don't want to continue discussing them
            else:
                # check if document is being discussed for too long; if yes, clear docs_in_use_info
                # do not check that if we have any document in attributes
                # if we get documents from build arguments (doc-processor-from-args),
                # N_TURNS_TO_KEEP_DOC should not be specified and then check is not performed
                if N_TURNS_TO_KEEP_DOC and not docs_in_atts:
                    # we are not checking anything unless n of turns in dialog >= N_TURNS_TO_KEEP_DOC
                    if len(all_prev_active_skills) >= N_TURNS_TO_KEEP_DOC:
                        prev_active_skills = set(all_prev_active_skills[n][-N_TURNS_TO_KEEP_DOC:])
                        # check if any SKILLS_USING_DOC are in prev_active_skills (if there is intersection)
                        intersection = SKILLS_USING_DOC & prev_active_skills
                        # if no SKILLS_USING_DOC were active recently, remove the doc from active memory
                        if not intersection:
                            docs_in_use_info.clear()
                            logger.info(
                                f"No skills using docs active for {N_TURNS_TO_KEEP_DOC} turns. \
Remove all docs from active memory."
                            )
            human_atts = {
                "human_attributes": {
                    "processed_documents": all_docs_info,
                    "documents_in_use": docs_in_use_info,
                    "documents_combination_ids": docs_combination_ids_info,
                }
            }
            attributes_to_add.append(human_atts)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            logger.exception(e)
            attributes_to_add.append({})
    return jsonify(attributes_to_add)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
