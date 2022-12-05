import json
import logging
from copy import deepcopy
from collections import Counter
from os import getenv

import numpy as np
import sentry_sdk
from nltk.tokenize import sent_tokenize

from common.greeting import greeting_spec
from common.link import skills_phrases_map
from common.constants import CAN_CONTINUE_PROMPT, CAN_CONTINUE_SCENARIO, MUST_CONTINUE, CAN_NOT_CONTINUE
from common.sensitive import is_sensitive_situation
from common.universal_templates import (
    if_chat_about_particular_topic,
    is_switch_topic,
    is_any_question_sentence_in_utterance,
    if_not_want_to_chat_about_particular_topic,
    if_choose_topic,
)
from common.utils import (
    get_intents,
    get_topics,
    get_entities,
    get_common_tokens_in_lists_of_strings,
    is_no,
    get_dialog_breakdown_annotations,
)
from utils import (
    how_are_you_spec,
    what_i_can_do_spec,
    misheard_with_spec1,
    misheard_with_spec2,
    join_used_links_in_attributes,
    get_updated_disliked_skills,
    LET_ME_ASK_YOU_PHRASES,
    downscore_if_question_to_question,
)
from common.response_selection import (
    ACTIVE_SKILLS,
    CAN_NOT_BE_DISLIKED_SKILLS,
    NOT_ADD_PROMPT_SKILLS,
)


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)

sentry_sdk.init(getenv("SENTRY_DSN"))
PRIORITIZE_WITH_SAME_TOPIC_ENTITY = int(getenv("PRIORITIZE_WITH_SAME_TOPIC_ENTITY", 1))
PRIORITIZE_NO_DIALOG_BREAKDOWN = int(getenv("PRIORITIZE_NO_DIALOG_BREAKDOWN", 0))
PRIORITIZE_WITH_REQUIRED_ACT = int(getenv("PRIORITIZE_WITH_REQUIRED_ACT", 0))
PRIORITIZE_HUMAN_INITIATIVE = int(getenv("PRIORITIZE_HUMAN_INITIATIVE", 0))
IGNORE_DISLIKED_SKILLS = int(getenv("IGNORE_DISLIKED_SKILLS", 0))
GREETING_FIRST = int(getenv("GREETING_FIRST", 1))
RESTRICTION_FOR_SENSITIVE_CASE = int(getenv("RESTRICTION_FOR_SENSITIVE_CASE", 1))
PRIORITIZE_PROMTS_WHEN_NO_SCRIPTS = int(getenv("PRIORITIZE_PROMTS_WHEN_NO_SCRIPTS", 1))
ADD_ACKNOWLEDGMENTS_IF_POSSIBLE = int(getenv("ADD_ACKNOWLEDGMENTS_IF_POSSIBLE", 1))
PROMPT_PROBA = float(getenv("PROMPT_PROBA", 0.3))
ACKNOWLEDGEMENT_PROBA = float(getenv("ACKNOWLEDGEMENT_PROBA", 0.5))
PRIORITIZE_SCRIPTED_SKILLS = int(getenv("PRIORITIZE_SCRIPTED_SKILLS", 1))
LANGUAGE = getenv("LANGUAGE", "EN")
MAX_TURNS_WITHOUT_SCRIPTS = int(getenv("MAX_TURNS_WITHOUT_SCRIPTS", 5))

force_intents_fname = "force_intents_intent_catcher.json"
FORCE_INTENTS_IC = json.load(open(force_intents_fname))

lets_chat_about_triggers_fname = "lets_chat_about_triggers.json"
LETS_CHAT_ABOUT_PARTICULAR_TOPICS = json.load(open(lets_chat_about_triggers_fname))

require_action_intents_fname = "require_action_intents.json"
REQUIRE_ACTION_INTENTS = json.load(open(require_action_intents_fname))

LINK_TO_PHRASES = sum([list(list_el) for list_el in skills_phrases_map.values()], [])

# this is a list of skills which are not one-lines
GENERAL_TOPICS = ["Phatic", "Other"]


def categorize_candidate(
    cand_id,
    skill_name,
    categorized_hyps,
    categorized_prompts,
    _is_just_prompt,
    _is_active_skill,
    _can_continue,
    _same_topic_entity,
    _is_dialog_abandon,
    _is_required_da=False,
):
    """Hypotheses could be:
        - active or not
        - can continue tag (not bool) out of CAN_CONTINUE_PROMPT, CAN_CONTINUE_SCENARIO,
                                             MUST_CONTINUE, CAN_NOT_CONTINUE
        - if has at least one of the same topic/named entity/noun phrase
        - is dialog breakdown or not
        - if contains required dialog act (required by user)

    Categories in priority order:
        = in terms of appropriateness when required dialog act:
            - reqda_same_topic_entity_no_db
            - reqda_same_topic_entity_db
            - reqda_othr_topic_entity_no_db
            - reqda_othr_topic_entity_db
            - else: TODO: here should be grounding skill with sorry about can not answer your request!
                - same_topic_entity_no_db
                - same_topic_entity_db
                - othr_topic_entity_no_db
                - othr_topic_entity_db
        = in terms of continuation of script:
            - active: active or not
            - continued: must_continue, can_continue_scenario, can_continue_scenario_done, can_not_continue
            - finished: one liners and finished scripts (can_not_continue)
        = in terms of appropriateness (user initiated switching topic and general case):
            - same_topic_entity_no_db
            - same_topic_entity_db
            - othr_topic_entity_no_db
            - othr_topic_entity_db
    """
    if (_can_continue == MUST_CONTINUE) or (_is_active_skill and PRIORITIZE_SCRIPTED_SKILLS):
        # so, scripted skills with CAN_CONTINUE_PROMPT status are not considered as active!
        # this is a chance for other skills to be turned on
        actsuffix = "active"
    elif _can_continue in [CAN_CONTINUE_SCENARIO, CAN_CONTINUE_PROMPT] and PRIORITIZE_SCRIPTED_SKILLS:
        actsuffix = "continued"
    else:
        actsuffix = "finished"

    if _same_topic_entity and not _is_dialog_abandon:
        # have at least one the same entity/topic/nounphrase, and NO dialog breakdown
        suffix = "same_topic_entity_no_db"
    elif _same_topic_entity and _is_dialog_abandon:
        # have at least one the same entity/topic/nounphrase, and dialog breakdown
        suffix = "same_topic_entity_db"
    elif not _is_dialog_abandon:
        # no same entity/topic/nounphrase, and NO dialog breakdown
        suffix = "othr_topic_entity_no_db"
    else:
        # no same entity/topic/nounphrase, and dialog breakdown
        suffix = "othr_topic_entity_db"

    if _is_required_da:
        dasuffix = "reqda"
    else:
        dasuffix = ""

    categorized_hyps[f"{actsuffix}_{suffix}_{dasuffix}"] += [cand_id]
    if _is_just_prompt:
        categorized_prompts[f"{actsuffix}_{suffix}_{dasuffix}"] += [cand_id]
    return categorized_hyps, categorized_prompts


def choose_best_with_scores(curr_cands_ids, curr_single_scores, candidates, bot_utterances):
    for i, cand_id in enumerate(curr_cands_ids):
        if candidates[cand_id]["skill_name"] in [
            "dummy_skill",
            "convert_reddit",
            "alice",
            "eliza",
            "tdidf_retrieval",
            "program_y",
        ]:
            if "question" in candidates[cand_id].get("type", "") or "?" in candidates[cand_id]["text"]:
                penalty_start_utt = 1
                if candidates[cand_id]["skill_name"] == "program_y":
                    penalty_start_utt = 4
                n_questions = 0
                if len(bot_utterances) >= penalty_start_utt and "?" in bot_utterances[-1]:
                    curr_single_scores[i] /= 1.5
                    n_questions += 1
                if len(bot_utterances) >= penalty_start_utt + 1 and "?" in bot_utterances[-2]:
                    curr_single_scores[i] /= 1.1
                    n_questions += 1
                if n_questions == 2:
                    # two subsequent questions (1 / (1.5 * 1.1 * 1.2) = ~0.5)
                    curr_single_scores[i] /= 1.2

    curr_scores = [curr_single_scores[i] for i in curr_cands_ids]
    best_id = np.argmax(curr_scores)
    return curr_cands_ids[best_id]


def get_main_info_annotations(annotated_utterance):
    intents = get_intents(annotated_utterance, which="all")
    topics = get_topics(annotated_utterance, which="all")
    named_entities = get_entities(annotated_utterance, only_named=True, with_labels=False)
    nounphrases = get_entities(annotated_utterance, only_named=False, with_labels=False)
    return intents, topics, named_entities, nounphrases


def pickup_best_id(categorized, candidates, curr_single_scores, bot_utterances):
    """Choose best hypotheses or prompt using priorities:
    - containing required dialog act, not containing required dialog act [second case also if
        user does not require particular dialog act];
    - active, continued, finished;
    - containing same topic/entity without dialog breakdown, containing same topic/entity with dialog breakdown,
        containing other topic/entity without dialog breakdown, containing other topic/entity with dialog breakdown.
    """
    best_cand_id = 0

    for dasuffix in ["reqda", ""]:
        # firstly, consider ACTIVE SKILL
        for actsuffix in ["active"]:
            for suffix in [
                "same_topic_entity_no_db",
                "same_topic_entity_db",
                "othr_topic_entity_no_db",
                "othr_topic_entity_db",
            ]:
                if len(categorized[f"{actsuffix}_{suffix}_{dasuffix}"]) > 0:
                    best_cand_id = choose_best_with_scores(
                        categorized[f"{actsuffix}_{suffix}_{dasuffix}"], curr_single_scores, candidates, bot_utterances
                    )
                    logger.info(f"==========Found {actsuffix}_{suffix}_{dasuffix} hyp: {candidates[best_cand_id]}")
                    return best_cand_id
        # secondly, consider all skills with the same topic/entities, priority those who can continue
        for actsuffix in ["continued", "finished"]:
            for suffix in ["same_topic_entity_no_db", "same_topic_entity_db"]:
                if len(categorized[f"{actsuffix}_{suffix}_{dasuffix}"]) > 0:
                    best_cand_id = choose_best_with_scores(
                        categorized[f"{actsuffix}_{suffix}_{dasuffix}"], curr_single_scores, candidates, bot_utterances
                    )
                    logger.info(f"==========Found {actsuffix}_{suffix}_{dasuffix} hyp: {candidates[best_cand_id]}")
                    return best_cand_id
        # thirdly, consider all skills with other topic/entities, priority those who can continue
        for actsuffix in ["continued", "finished"]:
            for suffix in ["othr_topic_entity_no_db", "othr_topic_entity_db"]:
                if len(categorized[f"{actsuffix}_{suffix}_{dasuffix}"]) > 0:
                    best_cand_id = choose_best_with_scores(
                        categorized[f"{actsuffix}_{suffix}_{dasuffix}"], curr_single_scores, candidates, bot_utterances
                    )
                    logger.info(f"==========Found {actsuffix}_{suffix}_{dasuffix} hyp: {candidates[best_cand_id]}")
                    return best_cand_id

    return best_cand_id


def prompt_decision():
    if np.random.uniform() < PROMPT_PROBA:
        return True
    return False


def acknowledgement_decision(all_user_intents):
    _is_user_opinion = "opinion" in all_user_intents
    if (_is_user_opinion and np.random.uniform() < ACKNOWLEDGEMENT_PROBA) or (
        not _is_user_opinion and np.random.uniform() < ACKNOWLEDGEMENT_PROBA / 5
    ):
        return True
    return False


def add_to_top1_category(cand_id, categorized, _is_require_action_intent):
    if _is_require_action_intent:
        categorized["active_same_topic_entity_no_db_reqda"].append(cand_id)
    else:
        categorized["active_same_topic_entity_no_db_"].append(cand_id)
    return categorized


def does_not_require_prompt(candidates, best_cand_id):
    _is_already_prompt = "prompt" in candidates[best_cand_id].get("response_parts", [])
    _is_very_long = len(candidates[best_cand_id]["text"]) > 100

    _best_cand_intents = get_intents(candidates[best_cand_id], which="all")
    _is_request = any([intent in _best_cand_intents for intent in REQUIRE_ACTION_INTENTS.keys()])
    _is_not_add_prompt_skill = candidates[best_cand_id]["skill_name"] in NOT_ADD_PROMPT_SKILLS

    _is_any_question = is_any_question_sentence_in_utterance(candidates[best_cand_id])
    _can_continue = (
        candidates[best_cand_id].get("can_continue", CAN_NOT_CONTINUE) != CAN_NOT_CONTINUE
        and candidates[best_cand_id]["skill_name"] in ACTIVE_SKILLS
    )
    if (
        _is_already_prompt
        or _is_very_long
        or _is_request
        or _is_not_add_prompt_skill
        or _is_any_question
        or _can_continue
    ):
        return True
    return False


def if_acknowledgement_in_previous_bot_utterance(dialog):
    if len(dialog["bot_utterances"]) > 0 and len(dialog["human_utterances"]) > 1:
        prev_bot_uttr_text = dialog["bot_utterances"][-1]["text"].lower()
        prev_human_uttr = dialog["human_utterances"][-2]
        acknowledgements = []
        for hyp in prev_human_uttr["hypotheses"]:
            if hyp.get("response_parts", []) == ["acknowledgement"]:
                acknowledgements += [hyp["text"].lower()]
        for ackn in acknowledgements:
            if ackn in prev_bot_uttr_text:
                return True
    return False


def rule_based_prioritization(cand_uttr, dialog):
    flag = False

    if (
        len(dialog["human_utterances"]) == 1
        and cand_uttr["skill_name"] == "dff_friendship_skill"
        and greeting_spec in cand_uttr["text"]
        and GREETING_FIRST
    ):
        # prioritize greeting phrase in the beginning of the dialog
        flag = True

    if (
        cand_uttr["skill_name"] == "small_talk_skill"
        and is_sensitive_situation(dialog["human_utterances"][-1])
        and RESTRICTION_FOR_SENSITIVE_CASE
    ):
        # small talk skill (if hypothesis is available) priority for sensitive situations when required
        flag = True
    if cand_uttr["skill_name"] == "misheard_asr" and any(
        [x in cand_uttr["text"] for x in [misheard_with_spec1, misheard_with_spec2]]
    ):
        # prioritize misheard_asr response when low ASR conf
        flag = True
    if cand_uttr["confidence"] >= 1.0:
        flag = True
    return flag


def tag_based_response_selection(
    dialog, candidates, curr_single_scores, confidences, bot_utterances, all_prev_active_skills=None
):
    all_prev_active_skills = all_prev_active_skills if all_prev_active_skills is not None else []
    prev_active_skills = all_prev_active_skills.copy()
    all_prev_active_skills = Counter(all_prev_active_skills)
    annotated_uttr = dialog["human_utterances"][-1]
    all_user_intents, all_user_topics, all_user_named_entities, all_user_nounphrases = get_main_info_annotations(
        annotated_uttr
    )

    _is_switch_topic_request = is_switch_topic(annotated_uttr)
    _is_force_intent = any([_intent in all_user_intents for _intent in FORCE_INTENTS_IC.keys()])
    # if user utterance contains any question (REGEXP & punctuation check!)
    _is_require_action_intent = is_any_question_sentence_in_utterance(
        {"text": annotated_uttr.get("annotations", {}).get("sentseg", {}).get("punct_sent", annotated_uttr["text"])}
    )
    # if user utterance contains any question AND requires some intent by socialbot
    _is_require_action_intent = _is_require_action_intent and any(
        [_intent in all_user_intents for _intent in REQUIRE_ACTION_INTENTS.keys()]
    )
    _force_intents_detected = [_intent for _intent in FORCE_INTENTS_IC.keys() if _intent in all_user_intents]
    # list of user intents which require some action by socialbot
    _require_action_intents_detected = [
        _intent for _intent in REQUIRE_ACTION_INTENTS.keys() if _intent in all_user_intents
    ]
    _force_intents_skills = sum([FORCE_INTENTS_IC.get(_intent, []) for _intent in _force_intents_detected], [])
    # list of intents required by the socialbot
    _required_actions = sum(
        [REQUIRE_ACTION_INTENTS.get(_intent, []) for _intent in _require_action_intents_detected], []
    )
    _contains_entities = len(get_entities(annotated_uttr, only_named=False, with_labels=False)) > 0
    _is_active_skill_can_not_continue = False

    n_available_bot_uttr = len(dialog["bot_utterances"])
    _prev_active_skills = []
    for i in range(min(MAX_TURNS_WITHOUT_SCRIPTS, n_available_bot_uttr)):
        _prev_active_skills.append(dialog["bot_utterances"][-i - 1]["active_skill"])
    _no_scripts_n_times_in_a_row = all([skill not in ACTIVE_SKILLS for skill in _prev_active_skills])
    _no_scripts_n_times_in_a_row = _no_scripts_n_times_in_a_row and len(_prev_active_skills) > MAX_TURNS_WITHOUT_SCRIPTS

    _prev_bot_uttr = dialog["bot_utterances"][-1] if len(dialog["bot_utterances"]) > 0 else {}
    _prev_active_skill = dialog["bot_utterances"][-1]["active_skill"] if len(dialog["bot_utterances"]) > 0 else ""

    disliked_skills = get_updated_disliked_skills(dialog, can_not_be_disliked_skills=CAN_NOT_BE_DISLIKED_SKILLS)

    _is_dummy_linkto_available = any(
        [
            cand_uttr["skill_name"] == "dummy_skill" and cand_uttr.get("type", "") == "link_to_for_response_selector"
            for cand_uttr in candidates
        ]
    )

    categorized_hyps = {}
    categorized_prompts = {}
    for dasuffix in ["reqda", ""]:
        for actsuffix in ["active", "continued", "finished"]:
            for suffix in [
                "same_topic_entity_no_db",
                "same_topic_entity_db",
                "othr_topic_entity_no_db",
                "othr_topic_entity_db",
            ]:
                categorized_hyps[f"{actsuffix}_{suffix}_{dasuffix}"] = []
                categorized_prompts[f"{actsuffix}_{suffix}_{dasuffix}"] = []

    CASE = ""
    acknowledgement_hypothesis = {}

    for cand_id, cand_uttr in enumerate(candidates):
        if confidences[cand_id] == 0.0 and cand_uttr["skill_name"] not in ACTIVE_SKILLS:
            logger.info(f"Dropping cand_id: {cand_id} due to toxicity/badlists")
            continue
        skill_name = cand_uttr["skill_name"]
        confidence = confidences[cand_id]
        score = curr_single_scores[cand_id]

        if (
            (skill_name in ACTIVE_SKILLS)
            and (skill_name in prev_active_skills)
            and (skill_name != prev_active_skills[-1])
        ):
            confidences[cand_id] *= 0.9

        logger.info(f"Skill {skill_name} has final score: {score}. Confidence: {confidence}.")

        all_cand_intents, all_cand_topics, all_cand_named_entities, all_cand_nounphrases = get_main_info_annotations(
            cand_uttr
        )
        skill_name = cand_uttr["skill_name"]
        _is_dialog_abandon = get_dialog_breakdown_annotations(cand_uttr) and PRIORITIZE_NO_DIALOG_BREAKDOWN
        _is_just_prompt = cand_uttr.get("response_parts", []) == ["prompt"]
        if cand_uttr["confidence"] == 1.0:
            # for those hypotheses where developer forgot to set tag to MUST_CONTINUE
            cand_uttr["can_continue"] = MUST_CONTINUE
        _can_continue = cand_uttr.get("can_continue", CAN_NOT_CONTINUE)

        _user_wants_to_chat_about_topic = (
            if_chat_about_particular_topic(annotated_uttr) and "about it" not in annotated_uttr["text"].lower()
        )
        _user_does_not_want_to_chat_about_topic = if_not_want_to_chat_about_particular_topic(annotated_uttr)
        _user_wants_bot_to_choose_topic = if_choose_topic(annotated_uttr, _prev_bot_uttr)

        if any([phrase.lower() in cand_uttr["text"].lower() for phrase in LINK_TO_PHRASES]):
            # add `prompt` to response_parts if any linkto phrase in hypothesis
            cand_uttr["response_parts"] = cand_uttr.get("response_parts", []) + ["prompt"]

        # identifies if candidate contains named entities from last human utterance
        _same_named_entities = (
            len(get_common_tokens_in_lists_of_strings(all_cand_named_entities, all_user_named_entities)) > 0
        )
        # identifies if candidate contains all (not only named) entities from last human utterance
        _same_nounphrases = len(get_common_tokens_in_lists_of_strings(all_cand_nounphrases, all_user_nounphrases)) > 0
        _same_topic_entity = (_same_named_entities or _same_nounphrases) and PRIORITIZE_WITH_SAME_TOPIC_ENTITY

        _is_active_skill = (
            _prev_active_skill == cand_uttr["skill_name"] or cand_uttr.get("can_continue", "") == MUST_CONTINUE
        )
        _is_active_skill = _is_active_skill and skill_name in ACTIVE_SKILLS
        _is_active_skill = _is_active_skill and (
            _can_continue in [MUST_CONTINUE, CAN_CONTINUE_SCENARIO, CAN_NOT_CONTINUE]
            or (_can_continue == CAN_CONTINUE_PROMPT and all_prev_active_skills.get(skill_name, []) < 10)
        )
        _is_active_skill = _is_active_skill or (skill_name in _force_intents_skills and _is_force_intent)
        _is_active_skill = _is_active_skill and PRIORITIZE_SCRIPTED_SKILLS
        if _is_active_skill:
            # we will forcibly add prompt if current scripted skill finishes scenario,
            # and has no opportunity to continue at all.
            _is_active_skill_can_not_continue = _is_active_skill and _can_continue in [CAN_NOT_CONTINUE]

        if _is_force_intent:
            # =====force intents, choose as best_on_topic hypotheses from skills responding this request=====

            CASE = "Force intent."
            categorized_hyps, categorized_prompts = categorize_candidate(
                cand_id,
                skill_name,
                categorized_hyps,
                categorized_prompts,
                _is_just_prompt,
                _is_active_skill,
                _can_continue,
                _same_topic_entity,
                _is_dialog_abandon,
                _is_required_da=False,
            )

        elif _is_switch_topic_request or _user_does_not_want_to_chat_about_topic or _user_wants_bot_to_choose_topic:
            # =====direct request by user to switch the topic of current conversation=====
            # give priority to dummy linkto hypothesis if available, else other prompts if available.
            _is_active_skill = (
                cand_uttr.get("type", "") == "link_to_for_response_selector"
                if _is_dummy_linkto_available
                else _is_just_prompt
            )
            # no priority to must_continue to skip incorrect continuation of script
            _can_continue = CAN_CONTINUE_SCENARIO if _can_continue == MUST_CONTINUE else _can_continue

            CASE = "Switch topic intent."
            if len(all_user_named_entities) > 0 or len(all_user_nounphrases) > 0:
                # -----user defines new topic/entity-----
                # _same_topic_entity does not depend on hyperparameter in these case
                _same_topic_entity = _same_named_entities or _same_nounphrases

                categorized_hyps, categorized_prompts = categorize_candidate(
                    cand_id,
                    skill_name,
                    categorized_hyps,
                    categorized_prompts,
                    _is_just_prompt,
                    _is_active_skill,
                    _can_continue,
                    _same_topic_entity,
                    _is_dialog_abandon,
                    _is_required_da=False,
                )
            else:
                # -----user want socialbot to define new topic/entity-----
                categorized_hyps, categorized_prompts = categorize_candidate(
                    cand_id,
                    skill_name,
                    categorized_hyps,
                    categorized_prompts,
                    _is_just_prompt,
                    _is_active_skill,
                    _can_continue,
                    _same_topic_entity,
                    _is_dialog_abandon,
                    _is_required_da=False,
                )

        elif _user_wants_to_chat_about_topic:
            # user wants to chat about particular topic

            CASE = "User wants to talk about topic."
            # in this case we do not give priority to previously active skill (but give to must continue skill!)
            # because now user wants to talk about something particular
            _is_active_skill = cand_uttr.get("can_continue", "") == MUST_CONTINUE
            # _same_topic_entity does not depend on hyperparameter in these case
            _same_topic_entity = _same_named_entities or _same_nounphrases

            categorized_hyps, categorized_prompts = categorize_candidate(
                cand_id,
                skill_name,
                categorized_hyps,
                categorized_prompts,
                _is_just_prompt,
                _is_active_skill,
                _can_continue,
                _same_topic_entity,
                _is_dialog_abandon,
                _is_required_da=False,
            )

        elif _is_require_action_intent and PRIORITIZE_WITH_REQUIRED_ACT:
            # =====user intent requires particular action=====

            CASE = "User intent requires action. USER UTTERANCE CONTAINS QUESTION."
            _is_grounding_reqda = (
                skill_name == "dff_grounding_skill" and cand_uttr.get("type", "") == "universal_response"
            )
            _is_active_skill = cand_uttr.get("can_continue", "") == MUST_CONTINUE  # no priority to prev active skill
            _can_continue = CAN_NOT_CONTINUE  # no priority to scripted skills

            if set(all_cand_intents).intersection(set(_required_actions)) or _is_grounding_reqda or _is_active_skill:
                # -----one of the can intent is in intents required by user-----
                categorized_hyps, categorized_prompts = categorize_candidate(
                    cand_id,
                    skill_name,
                    categorized_hyps,
                    categorized_prompts,
                    _is_just_prompt,
                    _is_active_skill,
                    _can_continue,
                    _same_topic_entity,
                    _is_dialog_abandon,
                    _is_required_da=True,
                )
            else:
                # -----NO required dialog acts-----
                categorized_hyps, categorized_prompts = categorize_candidate(
                    cand_id,
                    skill_name,
                    categorized_hyps,
                    categorized_prompts,
                    _is_just_prompt,
                    _is_active_skill,
                    _can_continue,
                    _same_topic_entity,
                    _is_dialog_abandon,
                    _is_required_da=False,
                )

        else:
            # =====user intent does NOT require particular action=====

            CASE = "General case."
            categorized_hyps, categorized_prompts = categorize_candidate(
                cand_id,
                skill_name,
                categorized_hyps,
                categorized_prompts,
                _is_just_prompt,
                _is_active_skill,
                _can_continue,
                _same_topic_entity,
                _is_dialog_abandon,
                _is_required_da=False,
            )

        # a bit of rule based help

        if (
            len(dialog["human_utterances"]) == 1
            and cand_uttr["skill_name"] == "dff_friendship_skill"
            and any([g in cand_uttr["text"] for g in greeting_spec.values()])
        ):
            categorized_hyps = add_to_top1_category(cand_id, categorized_hyps, _is_require_action_intent)
        elif (
            cand_uttr["skill_name"] == "dff_friendship_skill"
            and (how_are_you_spec in cand_uttr["text"] or what_i_can_do_spec in cand_uttr["text"])
            and len(dialog["utterances"]) < 16
            and PRIORITIZE_SCRIPTED_SKILLS
        ):
            categorized_hyps = add_to_top1_category(cand_id, categorized_hyps, _is_require_action_intent)
        # elif cand_uttr["skill_name"] == 'program_y_dangerous' and cand_uttr['confidence'] == 0.98:
        #     categorized_hyps = add_to_top1_category(cand_id, categorized_hyps, _is_require_action_intent)
        elif cand_uttr["skill_name"] == "small_talk_skill" and is_sensitive_situation(dialog["human_utterances"][-1]):
            # let small talk to talk about sex ^_^
            categorized_hyps = add_to_top1_category(cand_id, categorized_hyps, _is_require_action_intent)
        elif cand_uttr["confidence"] >= 1.0 and PRIORITIZE_SCRIPTED_SKILLS:
            # -------------------- SUPER CONFIDENCE CASE HERE! --------------------
            categorized_hyps = add_to_top1_category(cand_id, categorized_hyps, _is_require_action_intent)

        if cand_uttr["skill_name"] == "dff_grounding_skill" and ["acknowledgement"] == cand_uttr.get(
            "response_parts", []
        ):
            acknowledgement_hypothesis = deepcopy(cand_uttr)

    logger.info(f"Current CASE: {CASE}")
    # now compute current scores as one float value

    # remove disliked skills from hypotheses
    if IGNORE_DISLIKED_SKILLS:
        for category in categorized_hyps:
            new_ids = []
            for cand_id in categorized_hyps[category]:
                if (
                    candidates[cand_id]["skill_name"] in disliked_skills
                    and candidates[cand_id].get("can_continue", CAN_NOT_CONTINUE) == MUST_CONTINUE
                ):
                    disliked_skills.remove(candidates[cand_id]["skill_name"])
                if candidates[cand_id]["skill_name"] not in disliked_skills:
                    new_ids.append(cand_id)
            categorized_hyps[category] = deepcopy(new_ids)
        for category in categorized_prompts:
            new_ids = []
            for cand_id in categorized_prompts[category]:
                if (
                    candidates[cand_id]["skill_name"] in disliked_skills
                    and candidates[cand_id].get("can_continue", CAN_NOT_CONTINUE) == MUST_CONTINUE
                ):
                    disliked_skills.remove(candidates[cand_id]["skill_name"])
                if candidates[cand_id]["skill_name"] not in disliked_skills:
                    new_ids.append(cand_id)
            categorized_prompts[category] = deepcopy(new_ids)

    _is_question_by_user = is_any_question_sentence_in_utterance(dialog["human_utterances"][-1])
    if PRIORITIZE_HUMAN_INITIATIVE and _is_question_by_user:
        # downscore if hypothesis is a question in respond to a user's questions
        is_questions = [is_any_question_sentence_in_utterance(cand) for cand in candidates]
        curr_single_scores = downscore_if_question_to_question(curr_single_scores, is_questions)

    best_cand_id = pickup_best_id(categorized_hyps, candidates, curr_single_scores, bot_utterances)
    best_candidate = candidates[best_cand_id]
    best_candidate["human_attributes"] = best_candidate.get("human_attributes", {})
    # save updated disliked skills to human attributes of the best candidate
    best_candidate["human_attributes"]["disliked_skills"] = disliked_skills
    logger.info(f"Best candidate: {best_candidate}")
    n_sents_without_prompt = len(sent_tokenize(best_candidate["text"]))
    _is_best_not_script = best_candidate["skill_name"] not in ACTIVE_SKILLS

    # if `no` to 1st in a row linkto question, and chosen response is not from scripted skill
    _no_to_first_linkto = is_no(dialog["human_utterances"][-1]) and any(
        [phrase.lower() in _prev_bot_uttr.get("text", "").lower() for phrase in LINK_TO_PHRASES]
    )
    # if chosen short response or question by not-scripted skill
    _is_short_or_question_by_not_script = _is_best_not_script and (
        "?" in best_candidate["text"] or len(best_candidate["text"].split()) < 4
    )
    _no_questions_for_3_steps = (
        not any([is_any_question_sentence_in_utterance(uttr) for uttr in dialog["bot_utterances"][-3:]])
        and len(dialog["bot_utterances"]) >= 3
    )

    if PRIORITIZE_PROMTS_WHEN_NO_SCRIPTS:
        if (_no_scripts_n_times_in_a_row and _is_short_or_question_by_not_script and not _is_question_by_user) or (
            _no_to_first_linkto and _is_best_not_script
        ):
            logger.info(f"No prompts for {_no_scripts_n_times_in_a_row} times in a row.")
            # if no scripted skills 2 time sin a row before, current chosen best cand is not scripted, contains `?`,
            # and user utterance does not contain "?", replace utterance with dummy!
            best_prompt_id = pickup_best_id(categorized_prompts, candidates, curr_single_scores, bot_utterances)
            best_candidate = deepcopy(candidates[best_prompt_id])
            best_cand_id = best_prompt_id

    if does_not_require_prompt(candidates, best_cand_id):
        # the candidate already contains a prompt or a question or of a length more than 200 symbols
        logger.info("Best candidate contains prompt, question, request or length of > 200 symbols. Do NOT add prompt.")
        pass
    elif sum(categorized_prompts.values(), []):
        # best cand is 3d times in a row not scripted skill, let's append linkto

        # need to add some prompt, and have a prompt
        _add_prompt_forcibly = best_candidate["skill_name"] == _prev_active_skill and _is_active_skill_can_not_continue
        _add_prompt_forcibly = _add_prompt_forcibly and not _contains_entities

        # prompts are added:
        # - in 1 out of 10 cases, if current human utterance does not contain entities,
        # and no prompt for several last bot utterances
        # - if PRIORITIZE_PROMTS_WHEN_NO_SCRIPTS and current utterance is from active on prev step scripted skill and
        # it has a status can-not-continue
        # - if PRIORITIZE_PROMTS_WHEN_NO_SCRIPTS and last 2 bot uttr are not from scripted skill,
        # and current best uttr is also from not-scripted skill
        if (
            (prompt_decision() and not _contains_entities and _no_questions_for_3_steps)
            or (_add_prompt_forcibly and PRIORITIZE_PROMTS_WHEN_NO_SCRIPTS)
            or (PRIORITIZE_PROMTS_WHEN_NO_SCRIPTS and _no_scripts_n_times_in_a_row and _is_best_not_script)
        ):
            logger.info("Decided to add a prompt to the best candidate.")
            best_prompt_id = pickup_best_id(categorized_prompts, candidates, curr_single_scores, bot_utterances)
            # as we have only one active skill, let's consider active skill as that one providing prompt
            # but we also need to reassign all the attributes
            best_prompt = candidates[best_prompt_id]

            if "prelinkto_connections" in best_prompt.get("human_attributes", {}):
                # prelinkto connection phrase is already in the prompt (added in dummy skill)
                best_candidate["text"] = f'{best_candidate["text"]} {best_prompt["text"]}'
            else:
                prelinkto = np.random.choice(LET_ME_ASK_YOU_PHRASES[LANGUAGE])
                best_candidate["text"] = f'{best_candidate["text"]} {prelinkto} {best_prompt["text"]}'

            best_candidate["attributes"] = best_candidate.get("attributes", {})
            best_candidate["attributes"]["prompt_skill"] = best_prompt

            # anyway we must combine used links
            best_candidate["human_attributes"] = best_candidate.get("human_attributes", {})
            best_candidate["human_attributes"] = join_used_links_in_attributes(
                best_candidate["human_attributes"], best_prompt.get("human_attributes", {})
            )
            if len(best_candidate["human_attributes"]["used_links"]) == 0:
                best_candidate["human_attributes"].pop("used_links")

    was_ackn = if_acknowledgement_in_previous_bot_utterance(dialog)
    best_resp_cont_ackn = "acknowledgement" in best_candidate.get("response_parts", [])

    if (
        ADD_ACKNOWLEDGMENTS_IF_POSSIBLE
        and acknowledgement_hypothesis
        and acknowledgement_decision(all_user_intents)
        and n_sents_without_prompt == 1
        and not was_ackn
        and not best_resp_cont_ackn
    ):
        logger.info(
            "Acknowledgement is given, Final hypothesis contains only 1 sentence, no ackn in prev bot uttr,"
            "and we decided to add an acknowledgement to the best candidate."
        )
        best_candidate["text"] = f'{acknowledgement_hypothesis["text"]} {best_candidate["text"]}'
        best_candidate["response_parts"] = ["acknowledgement"] + best_candidate.get("response_parts", [])

    new_response = f"{best_candidate['skill_name']}: {best_candidate['text']}\n\n"
    new_response += "\n".join(
        [
            f"{cand['skill_name']} conf={confidences[cand_id]:.2f} "
            f"score={curr_single_scores[cand_id]:.2f}\t>>\t{cand['text']}"
            for cand_id, cand in enumerate(candidates)
            if len(cand["text"].strip()) > 0
        ]
    )
    logger.info(new_response)

    if "#+#" in best_candidate["text"]:
        best_candidate["text"] = best_candidate["text"][: best_candidate["text"].find("#+#")].strip()
    return best_candidate, best_cand_id, curr_single_scores
