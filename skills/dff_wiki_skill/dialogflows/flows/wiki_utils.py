import logging
import random
import re
import common.constants as common_constants
import common.dialogflow_framework.utils.state as state_utils
from common.dialogflow_framework.utils.condition import if_was_prev_active
from common.utils import is_no, is_yes
from common.wiki_skill import find_entity_wp, find_entity_nounphr, if_switch_wiki_skill, if_must_switch
from common.wiki_skill import CONF_DICT, QUESTION_TEMPLATES
from common.wiki_skill import choose_title, find_all_titles, find_paragraph
from common.insert_scenario import (
    get_page_content,
    get_page_title,
    get_titles,
    make_facts_str,
    titles_by_type,
    titles_by_entity_substr,
)
from common.universal_templates import COMPILE_NOT_WANT_TO_TALK_ABOUT_IT, is_any_question_sentence_in_utterance

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)

GO_TO_MAIN_PAGE = True
ANIMAL_TYPES_SET = {"Q16521", "Q55983715", "Q38547", "Q39367", "Q43577"}


def save_wiki_vars(
    vars,
    found_entity_substr_list,
    curr_pages,
    prev_title,
    prev_page_title,
    used_titles,
    found_entity_types_list,
    new_page,
):
    state_utils.save_to_shared_memory(vars, found_entity_substr=found_entity_substr_list)
    state_utils.save_to_shared_memory(vars, curr_pages=curr_pages)
    state_utils.save_to_shared_memory(vars, prev_title=prev_title)
    state_utils.save_to_shared_memory(vars, prev_page_title=prev_page_title)
    state_utils.save_to_shared_memory(vars, used_titles=used_titles)
    state_utils.save_to_shared_memory(vars, found_entity_types=list(found_entity_types_list))
    state_utils.save_to_shared_memory(vars, new_page=new_page)


def make_question(chosen_title, titles_q, found_entity_substr, used_titles):
    if chosen_title in titles_q and titles_q[chosen_title]:
        question = titles_q[chosen_title].format(found_entity_substr)
    else:
        if len(used_titles) == 1:
            question_template = QUESTION_TEMPLATES[0]
        else:
            question_template = random.choice(QUESTION_TEMPLATES)
        if (
            found_entity_substr in chosen_title.lower() and question_template.endswith("of {}?")
        ) or " of " in chosen_title.lower():
            question_template = question_template.split(" of {}?")[0] + "?"
            question = question_template.format(chosen_title)
        else:
            question = question_template.format(chosen_title, found_entity_substr)
    question = question.replace(" of of ", " of ")
    return question


def get_title_info(vars, found_entity_substr, found_entity_types, prev_title, used_titles, page_content):
    shared_memory = state_utils.get_shared_memory(vars)
    curr_pages = shared_memory.get("curr_pages", [])
    all_titles = find_all_titles([], page_content)
    titles_we_use = []
    for tp in found_entity_types:
        titles_we_use += list(titles_by_type.get(tp, {}).keys())
    titles_we_use += list(titles_by_entity_substr.get(found_entity_substr, {}).keys())

    logger.info(f"all_titles {all_titles}")
    chosen_title, chosen_page_title = choose_title(vars, all_titles, titles_we_use, prev_title, used_titles, curr_pages)
    return chosen_title, chosen_page_title


def another_topic_question(vars, all_titles):
    flag = True
    shared_memory = state_utils.get_shared_memory(vars)
    curr_pages = shared_memory.get("curr_pages", [])
    found_entity_substr_list = shared_memory.get("found_entity_substr", [])
    used_titles = shared_memory.get("used_titles", [])
    annotations = state_utils.get_last_human_utterance(vars)["annotations"]
    nounphrases = annotations.get("cobot_nounphrases", [])
    for nounphr in nounphrases:
        if (
            any([nounphr in curr_page.lower() for curr_page in curr_pages])
            or any([nounphr in entity_substr for entity_substr in found_entity_substr_list])
            or any([nounphr in title.lower() for title in used_titles])
            or any([nounphr in title.lower() for title in all_titles])
        ):
            flag = False
    logger.info(f"another topic question {another_topic_question}")
    return flag


def if_wants_more(vars, all_titles):
    flag = False
    isyes = is_yes(state_utils.get_last_human_utterance(vars))
    isno = is_no(state_utils.get_last_human_utterance(vars))
    user_uttr = state_utils.get_last_human_utterance(vars)
    further = re.findall(r"(more|further|continue|follow)", user_uttr["text"], re.IGNORECASE)
    another_topic = another_topic_question(vars, all_titles)
    if isyes or (further and not isno):
        flag = True
    if another_topic and not isyes:
        flag = False
    if isno:
        flag = False
    logger.info(f"wants_more={flag}")
    return flag


def make_response(vars, prev_page_title, page_content, question):
    mentions_list = []
    mention_pages_list = []
    facts_str = ""
    if prev_page_title:
        paragraphs = find_paragraph(page_content, prev_page_title)
        facts_str, mentions_list, mention_pages_list = make_facts_str(paragraphs)
    logger.info(f"facts_str {facts_str} question {question}")
    response = f"{facts_str} {question}"
    response = response.strip()
    state_utils.save_to_shared_memory(vars, mentions=mentions_list)
    state_utils.save_to_shared_memory(vars, mention_pages=mention_pages_list)
    return response


def find_entity(vars, where_to_find="current"):
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    if where_to_find == "current":
        annotations = state_utils.get_last_human_utterance(vars)["annotations"]
        found_entity_substr, found_entity_id, found_entity_types, _ = find_entity_wp(annotations, bot_uttr)
        if not found_entity_substr:
            found_entity_substr, _ = find_entity_nounphr(annotations)
    else:
        all_user_uttr = vars["agent"]["dialog"]["human_utterances"]
        utt_num = len(all_user_uttr)
        found_entity_substr = ""
        found_entity_types = []
        found_entity_id = ""
        if utt_num > 1:
            for i in range(utt_num - 2, 0, -1):
                annotations = all_user_uttr[i]["annotations"]
                found_entity_substr, found_entity_id, found_entity_types, _ = find_entity_wp(annotations, bot_uttr)
                if not found_entity_substr:
                    found_entity_substr, _ = find_entity_nounphr(annotations)
                if found_entity_substr:
                    break
    logger.info(f"find_entity, substr {found_entity_substr} types {found_entity_types}")
    return found_entity_substr, found_entity_id, found_entity_types


def get_page_info(vars, function_type, where_to_find="current"):
    shared_memory = state_utils.get_shared_memory(vars)
    curr_pages = shared_memory.get("curr_pages", [])
    found_entity_substr_list = shared_memory.get("found_entity_substr", [])
    prev_title = shared_memory.get("prev_title", "")
    prev_page_title = shared_memory.get("prev_page_title", "")
    used_titles = shared_memory.get("used_titles", [])
    found_entity_types_list = shared_memory.get("found_entity_types", [])
    started = shared_memory.get("start", False)
    was_prev_active = if_was_prev_active(vars)
    logger.info(f"started {started}")
    if function_type == "response" and curr_pages and found_entity_substr_list and found_entity_types_list:
        page_content, _ = get_page_content(curr_pages[-1])
        all_titles = find_all_titles([], page_content)
        wants_more = if_wants_more(vars, all_titles)
        logger.info(f"deleting, function_type {function_type} wants_more {wants_more}")
        if not wants_more:
            curr_pages.pop()
            found_entity_substr_list.pop()
            found_entity_types_list.pop()
    if not started or not was_prev_active:
        curr_pages = []
        found_entity_substr_list = []
        found_entity_types_list = []
        state_utils.save_to_shared_memory(vars, start=False)
    new_page = shared_memory.get("new_page", False)
    page_content_list = []
    main_pages_list = []
    if curr_pages:
        for page in curr_pages[-2:]:
            page_content, main_pages = get_page_content(page)
            page_content_list.append(page_content)
            main_pages_list.append(main_pages)
    else:
        found_entity_substr, _, found_entity_types = find_entity(vars, where_to_find)
        curr_page = get_page_title(vars, found_entity_substr)
        if curr_page:
            curr_pages.append(curr_page)
            found_entity_substr_list.append(found_entity_substr)
            found_entity_types_list.append(list(found_entity_types))
        for page in curr_pages[-2:]:
            page_content, main_pages = get_page_content(page)
            page_content_list.append(page_content)
            main_pages_list.append(main_pages)
    return (
        found_entity_substr_list,
        prev_title,
        prev_page_title,
        found_entity_types_list,
        used_titles,
        curr_pages,
        page_content_list,
        main_pages_list,
        new_page,
    )


def if_tell_fact(vars):
    flag = False
    user_uttr = state_utils.get_last_human_utterance(vars)
    isno = is_no(state_utils.get_last_human_utterance(vars))
    (
        found_entity_substr_list,
        prev_title,
        prev_page_title,
        found_entity_types_list,
        used_titles,
        _,
        page_content_list,
        main_pages_list,
        page,
    ) = get_page_info(vars, "request")
    logger.info(
        f"request, found_entity_substr {found_entity_substr_list} prev_title {prev_title} "
        f"found_entity_types {found_entity_types_list} used_titles {used_titles}"
    )
    shared_memory = state_utils.get_shared_memory(vars)
    started = shared_memory.get("start", False)
    shared_state = vars["agent"]["dff_shared_state"]
    logger.info(f"shared_state {shared_state}")
    if found_entity_substr_list and found_entity_types_list and page_content_list:
        chosen_title, chosen_page_title = get_title_info(
            vars,
            found_entity_substr_list[-1],
            found_entity_types_list[-1],
            prev_title,
            used_titles,
            page_content_list[-1],
        )
        _, _, all_titles = get_titles(found_entity_substr_list[-1], found_entity_types_list[-1], page_content_list[-1])
        logger.info(f"request, chosen_title {chosen_title} chosen_page_title {chosen_page_title}")
        wants_more = if_wants_more(vars, all_titles)
        not_want = re.findall(COMPILE_NOT_WANT_TO_TALK_ABOUT_IT, user_uttr["text"])

        if (chosen_title or prev_title) and (
            (wants_more and not not_want) or not started or len(found_entity_substr_list) > 1
        ):
            flag = True
        if user_uttr["text"].endswith("?") and another_topic_question(vars, all_titles):
            flag = False
    if isno:
        flag = False
    return flag


def make_fact_response(vars):
    shared_memory = state_utils.get_shared_memory(vars)
    user_uttr = state_utils.get_last_human_utterance(vars)
    bot_uttr = state_utils.get_last_bot_utterance(vars)
    (
        found_entity_substr_list,
        prev_title,
        prev_page_title,
        found_entity_types_list,
        used_titles,
        curr_pages,
        page_content_list,
        main_pages_list,
        new_page,
    ) = get_page_info(vars, "response")
    logger.info(
        f"tell_fact_response, found_entity_substr {found_entity_substr_list} prev_title {prev_title} "
        f"prev_page_title {prev_page_title} found_entity_types {found_entity_types_list} used_titles "
        f"{used_titles} curr_pages {curr_pages}"
    )
    titles_q, titles_we_use, all_titles = {}, [], []
    if found_entity_substr_list and found_entity_types_list and page_content_list:
        titles_q, titles_we_use, all_titles = get_titles(
            found_entity_substr_list[-1], found_entity_types_list[-1], page_content_list[-1]
        )
    logger.info(f"all_titles {all_titles} titles_q {titles_q} titles_we_use {titles_we_use}")
    chosen_title, chosen_page_title = choose_title(vars, all_titles, titles_we_use, prev_title, used_titles, curr_pages)
    logger.info(f"chosen_title {chosen_title} main_pages {main_pages_list}")
    if chosen_title:
        new_page = False
        if GO_TO_MAIN_PAGE and not any(
            [set(found_entity_types).intersection(ANIMAL_TYPES_SET) for found_entity_types in found_entity_types_list]
        ):
            chosen_main_pages = main_pages_list[-1].get(chosen_page_title, [])
            if chosen_main_pages:
                chosen_main_page = random.choice(chosen_main_pages)
                curr_pages.append(chosen_main_page)
                new_page = True
                found_entity_substr_list.append(chosen_main_page.lower())
                found_entity_types_list.append([])
        used_titles.append(chosen_title)
        save_wiki_vars(
            vars,
            found_entity_substr_list,
            curr_pages,
            chosen_title,
            chosen_page_title,
            used_titles,
            found_entity_types_list,
            new_page,
        )
    else:
        save_wiki_vars(vars, [], [], "", "", [], [], False)

    question = ""
    if found_entity_substr_list and chosen_title:
        question = make_question(chosen_title, titles_q, found_entity_substr_list[-1], used_titles)
    if new_page:
        if len(page_content_list) == 1:
            response = make_response(vars, prev_page_title, page_content_list[-1], question)
        else:
            response = make_response(vars, prev_page_title, page_content_list[-2], question)
    else:
        response = make_response(vars, prev_page_title, page_content_list[-1], question)
    started = shared_memory.get("start", False)
    has_q = is_any_question_sentence_in_utterance(user_uttr) and not re.findall(r"(let's|let us)", user_uttr["text"])
    _, conf_type = if_switch_wiki_skill(user_uttr, bot_uttr)

    cross_link = state_utils.get_cross_link(vars, service_name="dff_wiki_skill")
    from_skill = cross_link.get("from_service", "")
    if from_skill:
        state_utils.save_to_shared_memory(vars, interrupted_skill=from_skill)

    interrupted_skill = shared_memory.get("interrupted_skill", "")
    logger.info(f"interrupted_skill {interrupted_skill}")
    if interrupted_skill:
        state_utils.set_cross_link(vars, to_service_name=interrupted_skill, from_service_name="dff_wiki_skill")

    must_switch = if_must_switch(user_uttr, bot_uttr)
    if response:
        if not started and has_q:
            state_utils.set_confidence(vars, confidence=CONF_DICT["USER_QUESTION_IN_BEGIN"])
            state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_PROMPT)
        else:
            if not started:
                state_utils.set_confidence(vars, confidence=CONF_DICT[conf_type])
            else:
                state_utils.set_confidence(vars, confidence=CONF_DICT["IN_SCENARIO"])
            if interrupted_skill or must_switch:
                state_utils.set_can_continue(vars, continue_flag=common_constants.MUST_CONTINUE)
            else:
                state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_CONTINUE_SCENARIO)

        state_utils.save_to_shared_memory(vars, start=True)
    else:
        state_utils.set_confidence(vars, confidence=CONF_DICT["UNDEFINED"])
        state_utils.set_can_continue(vars, continue_flag=common_constants.CAN_NOT_CONTINUE)
    return response
