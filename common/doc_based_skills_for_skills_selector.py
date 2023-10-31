import logging
import sentry_sdk
from os import getenv
from typing import List

sentry_sdk.init(getenv("SENTRY_DSN"))
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def num_of_steps_with_same_doc(last_n_used_docs: List[List[str]], docs_in_use: List[str]) -> int:
    count = 0
    for doc_to_check in list(reversed(last_n_used_docs))[1:]:
        if doc_to_check == docs_in_use:
            count += 1
        else:
            break
    return count


def turn_on_doc_based_skills(
    dialog: dict,
    all_skill_names: List[str],
    selected_skills: List[str],
    prev_used_docs: List[str] = None,
    prev_active_skills: List[str] = None,
    auto_turn_on_meeting_analysis_when_doc_in_use: bool = True,
) -> List[str]:
    docs_in_use = dialog.get("human", {}).get("attributes", {}).get("documents_in_use", [])
    if docs_in_use:
        # if we have doc in use now, we always add dff_document_qa_llm_skill to selected skills
        if "dff_document_qa_llm_skill" in all_skill_names:
            logger.info("Document in use found. Turn on dff_document_qa_llm_skill.")
            selected_skills.append("dff_document_qa_llm_skill")
        if "dff_meeting_analysis_skill" in all_skill_names:
            # in some cases (description_based_skill_selector), we want to turn on
            # dff_meeting_analysis_skill always if we have doc in use
            if auto_turn_on_meeting_analysis_when_doc_in_use:
                logger.info("Document in use found. Turn on dff_meeting_analysis_skill.")
                selected_skills.append("dff_meeting_analysis_skill")
            # in other cases (llm_based_skill_selector), we perform a more complicated check
            else:
                # if we haven't selected dff_meeting_analysis_skill, check that we used it
                # with the same doc recently. if yes, append it to selected skills automatically
                if "dff_meeting_analysis_skill" not in selected_skills and prev_used_docs and prev_active_skills:
                    # count in how many steps was the active doc present
                    steps_with_same_doc = num_of_steps_with_same_doc(prev_used_docs, docs_in_use)
                    # get all skills that were active when the same doc was present
                    last_active_skills_with_same_doc = prev_active_skills[-steps_with_same_doc:]
                    # if we have doc in use and dff_meeting_analysis_skill was used earlier with the same doc,
                    # we add dff_meeting_analysis_skill
                    if "dff_meeting_analysis_skill" in last_active_skills_with_same_doc:
                        logger.info(
                            "Document in use found and dff_meeting_analysis_skill was used for this doc earlier. \
Turn on dff_meeting_analysis_skill."
                        )
                        selected_skills.append("dff_meeting_analysis_skill")
    return selected_skills
