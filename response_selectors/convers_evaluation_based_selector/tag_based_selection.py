import json
import logging
from copy import deepcopy
from os import getenv

import numpy as np
import sentry_sdk
from nltk.tokenize import sent_tokenize

from common.link import skills_phrases_map
from common.constants import CAN_CONTINUE_SCENARIO_DONE, CAN_CONTINUE_SCENARIO, MUST_CONTINUE, CAN_NOT_CONTINUE
from common.universal_templates import if_chat_about_particular_topic, is_switch_topic, \
    is_any_question_sentence_in_utterance
from common.utils import get_intent_name, get_intents, get_topics, get_common_tokens_in_lists_of_strings
from utils import calculate_single_convers_evaluator_score, CONV_EVAL_STRENGTH, CONFIDENCE_STRENGTH, \
    how_are_you_spec, what_i_can_do_spec, greeting_spec, misheard_with_spec1, \
    misheard_with_spec2, alexa_abilities_spec, join_used_links_in_attributes, get_updated_disliked_skills

sentry_sdk.init(getenv('SENTRY_DSN'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)

force_intents_fname = "force_intents_intent_catcher.json"
FORCE_INTENTS_IC = json.load(open(force_intents_fname))

lets_chat_about_triggers_fname = "lets_chat_about_triggers.json"
LETS_CHAT_ABOUT_PARTICULAR_TOPICS = json.load(open(lets_chat_about_triggers_fname))

require_action_intents_fname = "require_action_intents.json"
REQUIRE_ACTION_INTENTS = json.load(open(require_action_intents_fname))

PROMPT_PROBA = 0.3
ACKNOWLEDGEMENT_PROBA = 1.0

LINK_TO_PHRASES = sum([list(list_el) for list_el in skills_phrases_map.values()], [])

# this is a list of skills which are not one-lines
ACTIVE_SKILLS = [
    "book_skill", "christmas_new_year_skill", "coronaviruse_skill", "dummy_skill_dialog",
    "emotion_skill", "game_cooperative_skill",  # "knowledge_grounding_skill",
    "meta_script_skill", "movie_skill", "news_api_skill", "oscar_skill", "personal_info_skill",
    "reddit_ner_skill", "short_story_skill", "superbowl_skill",  # "small_talk_skill",
    "valentines_dat_skill", "weather_skill", "wikidata_dial_skill",  # "friendship_skill", "dff_friendship_skill",
    "comet_dialog_skill",
    "dff_animals_skill", "dff_food_skill", "dff_music_skill", "dff_sport_skill", "dff_travel_skill",
    "dff_celebrity_skill",
]
CAN_NOT_BE_DISLIKED_SKILLS = ["meta_script_skill", "personal_info_skill"]
NOT_ADD_PROMPT_SKILLS = ["alexa_handler", "intent_responder", "misheard_asr", "program_y_dangerous"]
GENERAL_TOPICS = ["Phatic", "Other"]


def categorize_candidate(cand_id, skill_name, categorized_hyps, categorized_prompts, _is_just_prompt,
                         _is_active_skill, _can_continue, _same_topic_entity, _is_dialog_abandon,
                         _is_required_da=False):
    """Hypotheses could be:
        - active or not
        - can continue tag (not bool) out of CAN_CONTINUE_SCENARIO_DONE, CAN_CONTINUE_SCENARIO,
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
    _is_active_skill = _is_active_skill and skill_name in ACTIVE_SKILLS
    if (_can_continue == MUST_CONTINUE) or (_is_active_skill and _can_continue == CAN_CONTINUE_SCENARIO):
        # so, scripted skills with CAN_CONTINUE_SCENARIO_DONE status are not considered as active!
        # this is a chance for other skills to be turned on
        actsuffix = "active"
    elif _can_continue in [CAN_CONTINUE_SCENARIO, CAN_CONTINUE_SCENARIO_DONE]:
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
        if candidates[cand_id]["skill_name"] in ["dummy_skill", "convert_reddit", "alice", "eliza",
                                                 "tdidf_retrieval", "program_y"]:
            if "question" in candidates[cand_id].get("type", "") or "?" in candidates[cand_id]['text']:
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
    named_entities = [ent[0]["text"] for ent in annotated_utterance.get("annotations", {}).get("ner", []) if ent]
    nounphrases = [nounph for nounph in annotated_utterance.get("annotations", {}).get("cobot_nounphrases", [])
                   if nounph]
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
        for actsuffix in ["active", "continued", "finished"]:
            for suffix in ["same_topic_entity_no_db", "same_topic_entity_db",
                           "othr_topic_entity_no_db", "othr_topic_entity_db"]:
                if len(categorized[f"{actsuffix}_{suffix}_{dasuffix}"]) > 0:
                    best_cand_id = choose_best_with_scores(categorized[f"{actsuffix}_{suffix}_{dasuffix}"],
                                                           curr_single_scores, candidates, bot_utterances)
                    logger.info(f"==========Found {actsuffix}_{suffix}_{dasuffix} hyp: {candidates[best_cand_id]}")
                    return best_cand_id

    return best_cand_id


def prompt_decision():
    if np.random.uniform() < PROMPT_PROBA:
        return True
    return False


def acknowledgement_decision():
    if np.random.uniform() < ACKNOWLEDGEMENT_PROBA:
        return True
    return False


def compute_curr_single_scores(candidates, scores, confidences):
    curr_single_scores = []

    for i in range(len(scores)):
        cand_scores = scores[i]
        confidence = confidences[i]
        skill_name = candidates[i]["skill_name"]
        score_conv_eval = calculate_single_convers_evaluator_score(cand_scores)
        score = CONV_EVAL_STRENGTH * score_conv_eval + CONFIDENCE_STRENGTH * confidence
        toxicity = max(candidates[i].get("annotations", {}).get('toxic_classification', {"toxic": 0.}).values())

        logger.info(f'Skill {skill_name} has final score: {score}. Confidence: {confidence}. '
                    f'Toxicity: {toxicity}. Cand scores: {cand_scores}')
        curr_single_scores.append(score)

    return curr_single_scores


def add_to_top1_category(cand_id, categorized, _is_require_action_intent):
    if _is_require_action_intent:
        categorized["active_same_topic_entity_no_db_reqda"].append(cand_id)
    else:
        categorized["active_same_topic_entity_no_db_"].append(cand_id)
    return categorized


def does_not_require_prompt(candidates, best_cand_id):
    _is_already_prompt = "prompt" in candidates[best_cand_id].get("response_parts", [])
    _is_question = "?" in candidates[best_cand_id]["text"]
    _is_very_long = len(candidates[best_cand_id]["text"]) > 200

    _best_cand_intents = get_intents(candidates[best_cand_id], which="all")
    _is_request = any([intent in _best_cand_intents for intent in REQUIRE_ACTION_INTENTS.keys()])
    _is_not_add_prompt_skill = candidates[best_cand_id]["skill_name"] in NOT_ADD_PROMPT_SKILLS

    _is_any_question = is_any_question_sentence_in_utterance(candidates[best_cand_id])
    _can_continue = candidates[best_cand_id].get("can_continue", CAN_NOT_CONTINUE) != CAN_NOT_CONTINUE
    if _is_already_prompt or _is_question or _is_very_long or _is_request or _is_not_add_prompt_skill or \
            _is_any_question or _can_continue:
        return True
    return False


def if_acknowledgement_in_previous_bot_utterance(dialog):
    if len(dialog["bot_utterances"]) > 0 and len(dialog["human_utterances"]) > 1:
        prev_bot_uttr_text = dialog["bot_utterances"][-1]["text"].lower()
        prev_human_uttr = dialog["human_utterances"][-2]
        acknowledgments = []
        for hyp in prev_human_uttr["hypotheses"]:
            if hyp.get("response_parts", []) == ["acknowledgment"]:
                acknowledgments += [hyp["text"].lower()]
        for ackn in acknowledgments:
            if ackn in prev_bot_uttr_text:
                return True
    return False


def tag_based_response_selection(dialog, candidates, scores, confidences, bot_utterances):
    annotated_uttr = dialog["human_utterances"][-1]
    all_user_intents, all_user_topics, all_user_named_entities, all_user_nounphrases = get_main_info_annotations(
        annotated_uttr)

    _is_switch_topic_request = is_switch_topic(annotated_uttr)
    _is_force_intent = any([_intent in all_user_intents for _intent in FORCE_INTENTS_IC.keys()])
    _is_require_action_intent = any([_intent in all_user_intents for _intent in REQUIRE_ACTION_INTENTS.keys()])
    _force_intents_detected = [_intent for _intent in FORCE_INTENTS_IC.keys() if _intent in all_user_intents]
    _require_action_intents_detected = [_intent for _intent in REQUIRE_ACTION_INTENTS.keys()
                                        if _intent in all_user_intents]
    _force_intents_skills = sum([FORCE_INTENTS_IC.get(_intent, [])
                                 for _intent in _force_intents_detected], [])
    _required_actions = sum([REQUIRE_ACTION_INTENTS.get(_intent, [])
                             for _intent in _require_action_intents_detected], [])

    if len(dialog["bot_utterances"]) > 0:
        _prev_active_skill = dialog["bot_utterances"][-1]["active_skill"]
    else:
        _prev_active_skill = ""

    disliked_skills = get_updated_disliked_skills(dialog, can_not_be_disliked_skills=CAN_NOT_BE_DISLIKED_SKILLS)

    categorized_hyps = {}
    categorized_prompts = {}
    for dasuffix in ["reqda", ""]:
        for actsuffix in ["active", "continued", "finished"]:
            for suffix in ["same_topic_entity_no_db", "same_topic_entity_db",
                           "othr_topic_entity_no_db", "othr_topic_entity_db"]:
                categorized_hyps[f"{actsuffix}_{suffix}_{dasuffix}"] = []
                categorized_prompts[f"{actsuffix}_{suffix}_{dasuffix}"] = []

    CASE = ""
    acknowledgement_hypothesis = {}

    for cand_id, cand_uttr in enumerate(candidates):

        all_cand_intents, all_cand_topics, all_cand_named_entities, all_cand_nounphrases = get_main_info_annotations(
            cand_uttr)
        skill_name = cand_uttr["skill_name"]
        _is_dialog_abandon = "abandon" in all_cand_intents
        _is_just_prompt = (cand_uttr["skill_name"] == "dummy_skill" and "link_to_for_response_selector" in
                           cand_uttr.get("type", "")) or cand_uttr.get("response_parts", []) == ["prompt"]
        _is_active_skill = (_prev_active_skill == cand_uttr["skill_name"] or cand_uttr.get(
            "can_continue", "") == MUST_CONTINUE)
        _user_wants_to_chat_about_topic = if_chat_about_particular_topic(
            dialog['utterances'][0]) and "about it" not in dialog['utterances'][0]["text"].lower()
        if any([phrase.lower() in cand_uttr["text"].lower() for phrase in LINK_TO_PHRASES]):
            # add `prompt` to response_parts if any linkto phrase in hypothesis
            cand_uttr["response_parts"] = cand_uttr.get("response_parts", []) + ["prompt"]

        _same_topics = set(all_cand_topics).intersection(set(all_user_topics))
        _same_topics = len(_same_topics) > 0 and len(_same_topics.difference(set(GENERAL_TOPICS))) > 0
        _same_named_entities = len(get_common_tokens_in_lists_of_strings(all_cand_named_entities,
                                                                         all_user_named_entities)) > 0
        _same_nounphrases = len(get_common_tokens_in_lists_of_strings(all_cand_nounphrases,
                                                                      all_user_nounphrases)) > 0
        _same_topic_entity = _same_topics or _same_named_entities or _same_nounphrases

        if cand_uttr["skill_name"] == 'program_y' and cand_uttr['confidence'] == 0.98:
            cand_uttr["can_continue"] = CAN_CONTINUE_SCENARIO_DONE
        _can_continue = cand_uttr.get("can_continue", CAN_NOT_CONTINUE)

        if _is_force_intent:
            # =====force intents, choose as best_on_topic hypotheses from skills responding this request=====

            CASE = "Force intent."
            if cand_uttr["skill_name"] in _force_intents_skills:
                categorized_hyps, categorized_prompts = categorize_candidate(
                    cand_id, skill_name, categorized_hyps, categorized_prompts, _is_just_prompt,
                    _is_active_skill, _can_continue, _same_topic_entity, _is_dialog_abandon,
                    _is_required_da=False)

        elif _is_switch_topic_request:
            # =====direct request by user to switch the topic of current conversation=====

            CASE = "Switch topic intent."
            if len(all_user_named_entities) > 0 or len(all_user_nounphrases) > 0:
                # -----user defines new topic/entity-----

                categorized_hyps, categorized_prompts = categorize_candidate(
                    cand_id, skill_name, categorized_hyps, categorized_prompts, _is_just_prompt,
                    _is_active_skill, _can_continue, _same_topic_entity, _is_dialog_abandon,
                    _is_required_da=False)
            else:
                # -----user want socialbot to define new topic/entity-----

                categorized_hyps, categorized_prompts = categorize_candidate(
                    cand_id, skill_name, categorized_hyps, categorized_prompts, _is_just_prompt,
                    _is_active_skill, _can_continue, _same_topic_entity, _is_dialog_abandon,
                    _is_required_da=False)

        elif _user_wants_to_chat_about_topic:
            # user wants to chat about particular topic

            CASE = "User wants to talk about topic."
            categorized_hyps, categorized_prompts = categorize_candidate(
                cand_id, skill_name, categorized_hyps, categorized_prompts, _is_just_prompt,
                _is_active_skill, _can_continue, _same_topic_entity, _is_dialog_abandon,
                _is_required_da=False)

        elif _is_require_action_intent:
            # =====user intent requires particular action=====

            CASE = "User intent requires action."
            if set(all_cand_intents).intersection(set(_required_actions)):
                # -----one of the can intent is in intents required by user-----
                categorized_hyps, categorized_prompts = categorize_candidate(
                    cand_id, skill_name, categorized_hyps, categorized_prompts, _is_just_prompt,
                    _is_active_skill, _can_continue, _same_topic_entity, _is_dialog_abandon,
                    _is_required_da=True)
            else:
                # -----NO required dialog acts-----
                categorized_hyps, categorized_prompts = categorize_candidate(
                    cand_id, skill_name, categorized_hyps, categorized_prompts, _is_just_prompt,
                    _is_active_skill, _can_continue, _same_topic_entity, _is_dialog_abandon,
                    _is_required_da=False)

        else:
            # =====user intent does NOT require particular action=====

            CASE = "General case."
            categorized_hyps, categorized_prompts = categorize_candidate(
                cand_id, skill_name, categorized_hyps, categorized_prompts, _is_just_prompt,
                _is_active_skill, _can_continue, _same_topic_entity, _is_dialog_abandon,
                _is_required_da=False)

        # a bit of rule based help
        is_misheard = misheard_with_spec1 in cand_uttr['text'] or misheard_with_spec2 in cand_uttr['text']
        intent_name = get_intent_name(cand_uttr['text'])
        is_intent_candidate = intent_name and cand_uttr["skill_name"] in ['intent_responder', 'program_y']
        if len(dialog['human_utterances']) == 1 and cand_uttr["skill_name"] == "dff_friendship_skill" and \
                greeting_spec in cand_uttr['text']:
            categorized_hyps = add_to_top1_category(cand_id, categorized_hyps, _is_require_action_intent)
        elif cand_uttr["skill_name"] == "dff_friendship_skill" and (
                how_are_you_spec in cand_uttr['text'] or what_i_can_do_spec in cand_uttr['text']) \
                and len(dialog['utterances']) < 16:
            categorized_hyps = add_to_top1_category(cand_id, categorized_hyps, _is_require_action_intent)
        elif cand_uttr["skill_name"] == 'program_y_dangerous' and cand_uttr['confidence'] == 0.98:
            categorized_hyps = add_to_top1_category(cand_id, categorized_hyps, _is_require_action_intent)
        elif cand_uttr["skill_name"] == 'weather_skill' and dialog['human_utterances'][-1]["annotations"].get(
                "intent_catcher", {}).get("weather_forecast_intent", {}).get("detected", 0) == 1:
            categorized_hyps = add_to_top1_category(cand_id, categorized_hyps, _is_require_action_intent)
        elif cand_uttr["skill_name"] == 'misheard_asr' and is_misheard:
            categorized_hyps = add_to_top1_category(cand_id, categorized_hyps, _is_require_action_intent)
        elif is_intent_candidate:
            categorized_hyps = add_to_top1_category(cand_id, categorized_hyps, _is_require_action_intent)
        elif cand_uttr["skill_name"] == "dff_friendship_skill" and alexa_abilities_spec in cand_uttr['text']:
            categorized_hyps = add_to_top1_category(cand_id, categorized_hyps, _is_require_action_intent)
        elif cand_uttr["confidence"] >= 1.:
            # -------------------- SUPER CONFIDENCE CASE HERE! --------------------
            categorized_hyps = add_to_top1_category(cand_id, categorized_hyps, _is_require_action_intent)

        if cand_uttr["skill_name"] == "grounding_skill" and "acknowledgement" in cand_uttr.get("response_parts", []):
            acknowledgement_hypothesis = deepcopy(cand_uttr)

    logger.info(f"Current CASE: {CASE}")
    # now compute current scores as one float value
    curr_single_scores = compute_curr_single_scores(candidates, scores, confidences)

    # remove disliked skills from hypotheses
    for category in categorized_hyps:
        new_ids = []
        for cand_id in categorized_hyps[category]:
            if candidates[cand_id]["skill_name"] not in disliked_skills:
                new_ids.append(cand_id)
        categorized_hyps[category] = deepcopy(new_ids)
    for category in categorized_prompts:
        new_ids = []
        for cand_id in categorized_prompts[category]:
            if candidates[cand_id]["skill_name"] not in disliked_skills:
                new_ids.append(cand_id)
        categorized_prompts[category] = deepcopy(new_ids)

    best_cand_id = pickup_best_id(categorized_hyps, candidates, curr_single_scores, bot_utterances)
    best_candidate = candidates[best_cand_id]
    best_candidate["human_attributes"] = best_candidate.get("human_attributes", {})
    # save updated disliked skills to human attributes of the best candidate
    best_candidate["human_attributes"]["disliked_skills"] = disliked_skills
    logger.info(f"Best candidate: {best_candidate}")
    n_sents_without_prompt = len(sent_tokenize(best_candidate["text"]))

    if does_not_require_prompt(candidates, best_cand_id):
        # the candidate already contains a prompt or a question or of a length more than 200 symbols
        logger.info(f"Best candidate contains prompt, question, request or length of > 200 symbols. "
                    f"Do NOT add prompt.")
        pass
    elif sum(categorized_prompts.values(), []):
        # need to add some prompt, and have a prompt
        if prompt_decision():
            logger.info(f"Decided to add a prompt to the best candidate.")
            best_prompt_id = pickup_best_id(categorized_prompts, candidates, curr_single_scores, bot_utterances)
            # as we have only one active skill, let's consider active skill as that one providing prompt
            # but we also need to reassign all the attributes
            best_prompt = candidates[best_prompt_id]
            best_candidate["text"] = f'{best_candidate["text"]} {best_prompt["text"]}'
            # TODO: how to correctly reassign human-/bot-/hyp- attributes??? how to deal with skill name?
            best_candidate["attributes"] = best_candidate.get("attributes", {})
            best_candidate["attributes"]["prompt_skill"] = best_prompt

            # anyway we must combine used links
            best_candidate["human_attributes"] = best_candidate.get("human_attributes", {})
            best_candidate["human_attributes"] = join_used_links_in_attributes(
                best_candidate["human_attributes"], best_prompt.get("human_attributes", {}))
            if len(best_candidate["human_attributes"]["used_links"]) == 0:
                best_candidate["human_attributes"].pop("used_links")

    was_ackn = if_acknowledgement_in_previous_bot_utterance(dialog)
    if acknowledgement_hypothesis and acknowledgement_decision() and n_sents_without_prompt == 1 and not was_ackn:
        logger.info(f"Acknowledgement is given, Final hypothesis contains only 1 sentence, no ackn in prev bot uttr,"
                    f"and we decided to add an acknowledgement to the best candidate.")
        best_candidate["text"] = f'{acknowledgement_hypothesis["text"]} {best_candidate["text"]}'
        best_candidate["response_parts"] = ["acknowledgement"] + best_candidate.get("response_parts", [])

    return best_candidate, best_cand_id, curr_single_scores
