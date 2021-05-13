# %%
import os
import logging
import random
from enum import Enum, auto
import re

import sentry_sdk


import common.dialogflow_framework.stdm.dialogflow_extention as dialogflow_extention
import common.dialogflow_framework.utils.state as state_utils
import common.dialogflow_framework.utils.condition as condition_utils
import common.utils as common_utils
import common.constants as common_constants
import common.news as general_common_news
from common.gossip import talk_about_gossip, skill_trigger_phrases

import dialogflows.scenarios.gossip as common_gossip
import dialogflows.scenarios.news as common_news

import dialogflows.scopes as scopes

from dialogflows.flows import utils


sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))
NEWS_API_ANNOTATOR_URL = os.environ.get("NEWS_API_ANNOTATOR_URL")
assert NEWS_API_ANNOTATOR_URL

logger = logging.getLogger(__name__)


class State(Enum):
    USR_START = auto()

    SYS_TOPIC_TO_EVENT = auto()
    USR_TOPIC_TO_EVENT = auto()

    SYS_NO_OR_YES = auto()
    USR_NO_OR_YES = auto()

    SYS_EVENT_TO_PERSON = auto()
    USR_EVENT_TO_PERSON = auto()

    # BEGIN: USR_NOT_INTERESTED_IN_PERSON
    SYS_NOT_INTERESTED_IN_PERSON = auto()
    USR_NOT_INTERESTED_IN_PERSON = auto()

    SYS_CHANGE_TO_PERSON = auto()
    USR_CHANGE_TO_PERSON = auto()
    # transitions back to:
    # NOT_INTERESTED_IN_PERSON
    # AGREES_ABT_PERSON
    # DISAGREES_ABT_PERSON
    # SAYS_OPINION_ABT_PERSON
    # END

    # BEGIN: USR_AGREES_ABT_PERSON
    SYS_AGREES_ABT_PERSON = auto()
    USR_AGREES_ABT_PERSON = auto()

    SYS_PERSON_AGREE = auto()
    USR_PERSON_AGREE = auto()

    SYS_SAYS_SOMETHING_AFTER_AGREE = auto()
    USR_SAYS_SOMETHING_AFTER_AGREE = auto()
    # transitions back to:
    # NOT_INTERESTED_IN_PERSON
    # AGREES_ABT_PERSON
    # DISAGREES_ABT_PERSON
    # SAYS_OPINION_ABT_PERSON
    # END

    # BEGIN
    SYS_DISAGREES_ABT_PERSON = auto()
    USR_DISAGREES_ABT_PERSON = auto()

    SYS_PERSON_DISAGREE = auto()
    USR_PERSON_DISAGREE = auto()

    SYS_SAYS_SOMETHING_AFTER_DISAGREE = auto()
    USR_SAYS_SOMETHING_AFTER_DISAGREE = auto()
    # transitions back to:
    # NOT_INTERESTED_IN_PERSON
    # AGREES_ABT_PERSON
    # DISAGREES_ABT_PERSON
    # SAYS_OPINION_ABT_PERSON
    # END

    # BEGIN: USR_SAYS_OPINION_ABT_PERSON
    SYS_SAYS_OPINION_ABT_PERSON = auto()
    USR_SAYS_OPINION_ABT_PERSON = auto()

    SYS_PERSON_OPINION = auto()
    USR_PERSON_OPINION = auto()

    SYS_SAYS_SOMETHING_AFTER_OPINION = auto()
    USR_SAYS_SOMETHING_AFTER_OPINION = auto()
    # transitions back to:
    # NOT_INTERESTED_IN_PERSON
    # AGREES_ABT_PERSON
    # DISAGREES_ABT_PERSON
    # SAYS_OPINION_ABT_PERSON
    # END

    SYS_MENTIONS_ANOTHER_PERSON = auto()
    USR_MENTIONS_ANOTHER_PERSON = auto()

    # Helpers: Error
    SYS_ERR = auto()
    USR_ERR = auto()

    # Helpers: End?
    SYS_END = auto()
    USR_END = auto()


# endregion


# region CONFIDENCES
DIALOG_BEGINNING_START_CONFIDENCE = 0.98
DIALOG_BEGINNING_CONTINUE_CONFIDENCE = 0.9
DIALOG_BEGINNING_SHORT_ANSWER_CONFIDENCE = 0.98
MIDDLE_DIALOG_START_CONFIDENCE = 0.7
SUPER_CONFIDENCE = 1.0
HIGH_CONFIDENCE = 0.98

MUST_CONTINUE_CONFIDENCE = 0.98
CANNOT_CONTINUE_CONFIDENCE = 0.0
# endregion

# endregion

################################################################################
# %%


##################################################################################################################
# Init DialogFlow
##################################################################################################################


simplified_dialogflow = dialogflow_extention.DFEasyFilling(State.USR_START)

##################################################################################################################
##################################################################################################################
# Design DialogFlow.
##################################################################################################################
##################################################################################################################
##################################################################################################################
# utils


def is_yes_request(ngrams, vars):
    if condition_utils.is_yes_vars(vars):
        return True
    return False


def is_no_request(ngrams, vars):
    if condition_utils.is_no_vars(vars):
        return True
    return False


def get_people_for_topic(cobot_topic):
    # human-curated list (top 10-20 for 2010s)
    peoples = [
        list(x.get("People", [])) for x in common_gossip.TOPICS_TO_PEOPLE_MAPPINGS if x.get("Topic", "") == cobot_topic
    ]
    peoples = list(set(sum(peoples, [])))
    # wikidata-based list
    top_people_from_wiki = utils.get_top_people_from_wiki_for_cobot_topic(cobot_topic, peoples)
    return top_people_from_wiki + peoples


def get_phrase_about_person_in_content(person, content):
    # TODO: "." for what?
    sentences_list = content.split(".")

    for sentence in sentences_list:
        if sentence.lower().count(person.lower()) > 0:
            return sentence


def save_mentioned_person(vars, person, judgement, share_memory_key):
    shared_memory = state_utils.get_shared_memory(vars)
    # "people_mentioned_by_bot"
    # obtaining a list of previously mentioned people
    all_mentioned_people = shared_memory.get(share_memory_key, [])
    if all(x.get("Judgement", "") != judgement for x in all_mentioned_people):
        all_mentioned_people += [{"Judgement": judgement, "People": []}]
    [people for people in all_mentioned_people if people.get("Judgement", "") == judgement][0].get("People", []).append(
        person
    )
    # saving
    state_utils.save_to_shared_memory(vars, **{share_memory_key: all_mentioned_people})


def get_mentioned_people(vars, share_memory_key="", judgements=["Liked", "Disliked", "Not Interested", "Other"]):
    shared_memory = state_utils.get_shared_memory(vars)
    # obtaining a list of previously mentioned people
    all_mentioned_people = shared_memory.get(share_memory_key, [])
    if all_mentioned_people:
        peoples = [list(x.get("People", [])) for x in all_mentioned_people if x.get("Judgement", "") in judgements]
        peoples = list(set(sum(peoples, [])))
        return peoples
    else:
        return []


# inefficient if number of people is finite
def get_fresh_person_for_topic(vars, cobot_topic):
    all_mentioned_people = set(get_mentioned_people(vars, share_memory_key="people_mentioned_by_bot"))
    topic_people = [
        list(i.get("People", [])) for i in common_gossip.TOPICS_TO_PEOPLE_MAPPINGS if i.get("Topic", "") == cobot_topic
    ]
    topic_people = sum(topic_people, [])
    topic_people = set(topic_people)
    topic_people = topic_people - all_mentioned_people
    if topic_people:
        return random.choice(list(topic_people))


def mark_news_as_mentioned_by_bot(vars, news_title):
    shared_memory = state_utils.get_shared_memory(vars)

    # obtaining a list of previously mentioned news
    all_mentioned_news = shared_memory.get("news_mentioned_by_bot", [])

    all_mentioned_news.append(news_title)
    # saving
    state_utils.save_to_shared_memory(vars, all_mentioned_news=all_mentioned_news)


def get_people_related_to_bot_mentioned_ones(vars, user_mentioned_people):
    # for the time being, we support only one user
    related_people = []

    if not user_mentioned_people:
        return related_people

    user_mentioned_person = user_mentioned_people[0]

    people_mentioned_and_liked_by_bot = get_mentioned_people(vars, "people_mentioned_by_bot", ["Liked", "Disliked"])

    for person in people_mentioned_and_liked_by_bot:
        relationship = utils.get_relationship_between_two_people(user_mentioned_person, person)
        if relationship:
            related_people.append([person, relationship])

    return related_people


def get_news_for_topic(vars, cobot_topic):
    people = get_people_for_topic(cobot_topic)
    mentioned_people = get_mentioned_people(vars, share_memory_key="people_mentioned_by_bot")
    people = [person for person in people if person not in mentioned_people]

    if people:
        person = random.choice(people)
        curr_news = general_common_news.get_news_about_topic(person, NEWS_API_ANNOTATOR_URL)
        logger.debug(f"news = {curr_news}")

        if curr_news and "content" in curr_news and "title" in curr_news:
            content = curr_news["content"].split("[")[0]
            title = curr_news["title"]

            if person.lower() in content.lower():
                logger.debug("random_person was mentioned in content")
                filtered_content = get_phrase_about_person_in_content(person.lower(), content.lower())
                return person, title, filtered_content
            elif person.lower() in title.lower():
                logger.debug("random_person was mentioned in title")
                return person, title, content

    topic_news = [
        list(i["News"]) for i in common_news.TEMPORARY_NEWS_FOR_COBOT_TOPICS if i.get("Topic", "") == cobot_topic
    ]
    topic_news = sum(topic_news, [])
    logger.debug(f"topic_news={topic_news}")
    if topic_news:
        random_news = random.choice(topic_news)
        person = random_news["Person"]
        title = random_news["Title"]
        content = random_news["Content"]
    else:
        person = ""
        title = ""
        content = ""

    return person, title, content


def get_random_judgement_for_emotion(emotion):
    judgements = [
        list(x.get("People", [])) for x in common_gossip.TARGET_JUDGEMENTS_FOR_EMOTION if x["Emotion"] in emotion
    ]
    judgements = list(set(sum(judgements, [])))
    return random.choice(judgements) if judgements else "Great"


supported_cobot_topics = [
    "Entertainment_Movies",
    "Entertainment_Music",
    "Entertainment_Books",
    "Sports",
    "Politics",
    "Entertainment_General",
    "Science_and_Technology",
]


def get_supported_cobot_topics(vars):
    topics = common_utils.get_topics(state_utils.get_last_human_utterance(vars), which="cobot_dialogact_topics")
    selected_topics = set(topics) & set(supported_cobot_topics)
    selected_topics = selected_topics if selected_topics else supported_cobot_topics
    return selected_topics


##################################################################################################################
# error
##################################################################################################################


def error_response(vars):
    logger.debug("exec error_response")
    state_utils.set_confidence(vars, CANNOT_CONTINUE_CONFIDENCE)
    state_utils.set_confidence(vars, 0)
    return ""


##################################################################################################################
# Handlers
##################################################################################################################


# region TOPIC_TO_EVENT
##################################################################################################################


def talk_about_gossip_request(ngrams, vars):
    human_utterance = state_utils.get_last_human_utterance(vars)
    bot_utterance = state_utils.get_last_bot_utterance(vars)
    flag = talk_about_gossip(human_utterance, bot_utterance)
    logger.info(f"talk_about_gossip_request: {flag}")
    return flag


def sys_topic_to_event_request(ngrams, vars):
    # we get here because user mentioned a topic, or we've got a topic
    # ok so let's for the time being believe that we are here by default - just because a topic was mentioned
    bot_utterance = state_utils.get_last_bot_utterance(vars)
    flag = (bool(get_supported_cobot_topics(vars)) and talk_about_gossip_request(ngrams, vars)) or (
        any([phrase in bot_utterance["text"] for phrase in skill_trigger_phrases()])
        and condition_utils.is_yes_vars(vars)
    )
    logger.info(f"sys_topic_to_event={flag}")
    return flag


def default_condition_request(ngrams, vars):
    flag = True
    flag = flag and not condition_utils.is_switch_topic(vars)
    flag = flag and not condition_utils.is_lets_chat_about_topic_human_initiative(vars)
    flag = flag and not condition_utils.is_question(vars)
    flag = flag or talk_about_gossip_request(ngrams, vars)
    return flag


def usr_topic_to_event_response(vars):
    # %ack%. So, speaking of %target_topic%, this happened recently: %event%. Have you heard about it?
    logger.debug("exec usr_topic_to_event_response")
    try:
        selected_topics = get_supported_cobot_topics(vars)
        if selected_topics:
            cobot_topic = random.choice(list(selected_topics))  # "Entertainment_Movies" # for the time being
        else:
            return error_response(vars)

        # obtaining person, news_title, news_content for a given cobot_topic
        person, news_title, news_content = get_news_for_topic(vars, cobot_topic)
        logger.debug(f"person = {person}, news_title = {news_title}, news_content = {news_content}, ")

        person = person.strip()
        if person and person.lower() in news_title.lower():
            logger.debug(f"News about {person} : {news_title}")
            event = news_title
        elif person and person.lower() in news_content.lower():
            logger.debug(f"News about {person} : It's said that {news_content}: {news_title}")
            event = news_content
        else:
            # for testing purposes only
            event = "Natasha Romanoff (Scarlett Johansson) is going back to where it all started"
            person = "Scarlett Johansson"
            news_title = "Disney will release Scarlett Johansson in Black Widow in theaters and streaming in July"

        # get ack, body
        ack = condition_utils.get_not_used_and_save_sentiment_acknowledgement(vars)

        # saving person to the list of people mentioned by bot, for now with "Other" judgement
        save_mentioned_person(vars, person, "Other", "people_mentioned_by_bot")
        # saving news as mentioned by bot
        mark_news_as_mentioned_by_bot(vars, news_title)

        state_utils.save_to_shared_memory(vars, current_person=person)

        # saving current cobot_topic
        state_utils.save_to_shared_memory(vars, current_cobot_topic=cobot_topic)

        # generating response

        topic = common_news.COBOT_TO_HUMAN_READABLE_TOPICS.get(cobot_topic)
        questions = common_gossip.TOPIC_TO_EVENT_QUESTIONS
        questions = questions if topic else [i for i in questions if "target_topic" not in i]
        questions = questions if event else [i for i in questions if "target_event" not in i]

        if not questions:
            return error_response(vars)

        body = random.choice(questions)

        body = body.replace("target_topic", topic) if topic else body
        body = body.replace("target_event", event)

        # set confidence
        state_utils.set_confidence(vars, SUPER_CONFIDENCE)
        # can continue = true
        state_utils.set_can_continue(vars, common_constants.MUST_CONTINUE)

        return " ".join([ack, body])
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


# endregion

# region NO_OR_YES
################################################################################


def sys_no_or_yes_request(ngrams, vars):
    logger.debug("sys_no_or_yes_request: BEGIN")
    flag = is_yes_request(ngrams, vars) or is_no_request(ngrams, vars)
    logger.info(f"sys_no_or_yes_request={flag}")
    return flag


def usr_event_to_person_response(vars):
    # %ack%. %Person% particularly interested me.
    # I %usuality_modulation_level% %Person% is a %complement% %occupation%.
    # %Judgement%. But... What do you think?
    logger.debug("exec usr_event_to_person_response")
    try:
        shared_memory = state_utils.get_shared_memory(vars)

        # obtaining current person
        current_person = shared_memory.get("current_person", "")
        current_cobot_topic = shared_memory.get("current_cobot_topic", "")

        # TEMPORARY OVERRIDE
        current_cobot_topic = "Entertainment_Movies"

        # Positive or Negative
        emotion_reaction_options = ["Liked", "Disliked"]
        # trusting holy RNG
        target_emotion_type = random.choice(emotion_reaction_options)
        target_judgement = get_random_judgement_for_emotion(target_emotion_type)

        # saving current bot's emotion towards the currently discussed person
        state_utils.save_to_shared_memory(vars, bot_emotion_towards_current_person=target_emotion_type)

        # get ack, body
        ack = condition_utils.get_not_used_and_save_sentiment_acknowledgement(vars)

        # generating response
        body = random.choice(common_gossip.EVENT_TO_PERSON_QUESTIONS)

        # putting actual person's name into an upcoming utterance
        body = body.replace("target_person", current_person)
        body = body.replace("target_judgement", target_judgement)

        # obtaining occupation (person/generic/wiki-based)
        occupation = utils.get_occupation_for_person(current_person, current_cobot_topic, body)

        logger.info(f"found occupation: {occupation}")

        # saving it
        state_utils.save_to_shared_memory(vars, current_person_occupation=occupation)

        # further updating body with the obtained occupation
        body = body.replace("target_occupation", occupation)

        # building prompt
        prompt = random.choice(common_gossip.AGREEMENT_PROMPTS)

        state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
        # can continue = true
        state_utils.set_can_continue(vars, common_constants.CAN_CONTINUE_SCENARIO)

        return " ".join([ack, body, prompt])
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


# endregion


# region LOOP #1: NOT_INTERESTED_IN_PERSON

# STEP 1
################################################################################


def sys_not_interested_in_person_request(ngrams, vars):
    flag = False
    human_utterance = state_utils.get_last_human_utterance(vars)

    sf_type, sf_confidence = utils.get_speech_function_for_human_utterance(human_utterance)
    logger.debug(f"sys_not_interested_in_person_request: Speech Function: {sf_type}")

    # using speech function classifier for not interested
    flag = utils.is_not_interested_speech_function(vars)
    flag = flag and default_condition_request(ngrams, vars)

    logger.info(f"sys_not_interested_in_person_request={flag}")
    return flag


def usr_not_interested_in_person_response(vars):
    logger.debug("exec usr_not_interested_in_person_response")
    try:

        shared_memory = state_utils.get_shared_memory(vars)
        # obtaining current context
        current_cobot_topic = shared_memory.get("current_cobot_topic", "")
        # getting human-readable version
        # TODO
        human_topic = common_news.COBOT_TO_HUMAN_READABLE_TOPICS.get(current_cobot_topic)

        # obtaining new random person + news for current cobot_topic
        person = get_fresh_person_for_topic(vars, current_cobot_topic)
        if not person:
            raise Exception(f"Have no fresh person for {current_cobot_topic}")

        # Positive or Negative
        emotion_reaction_options = ["Liked", "Disliked"]
        # trusting holy RNG
        target_emotion_type = random.choice(emotion_reaction_options)
        target_judgement = get_random_judgement_for_emotion(target_emotion_type)

        # saving current bot's emotion towards the currently discussed person
        state_utils.save_to_shared_memory(vars, bot_emotion_towards_current_person=target_emotion_type)

        # saving person to the list of people mentioned by bot, for now with "Other" judgement
        save_mentioned_person(vars, person, "Liked", "people_mentioned_by_bot")
        # setting current context (only person, we didn't change topic)
        state_utils.save_to_shared_memory(vars, current_person=person)

        # generating response
        ack = f"{random.choice(common_gossip.NOT_INTERESTED_IN_PERSON_ACKNOWLEDGEMENTS)}."
        prompt = random.choice(common_gossip.CHANGE_TO_OTHER_PERSON_QUESTIONS)

        # occupation
        occupation = utils.get_occupation_for_person(person, current_cobot_topic, prompt)

        fake_utterance = f"I like to learn more about {occupation} {person} {human_topic}"
        gender, age = utils.get_gender_age_person(person, fake_utterance)

        gender_is = utils.get_human_readable_gender_statement_current_is(gender)

        prompt = prompt.replace("target_person", person)
        prompt = prompt.replace("target_topic", human_topic)
        prompt = prompt.replace("target_judgement", target_judgement)
        prompt = prompt.replace("target_gender_is", gender_is)

        # saving it
        state_utils.save_to_shared_memory(vars, current_person_occupation=occupation)

        prompt = prompt.replace("target_occupation", occupation)

        state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
        state_utils.set_can_continue(vars, common_constants.CAN_CONTINUE_PROMPT)

        return " ".join([ack, prompt])
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


# endregion

# region LOOP #2: AGREES_ABT_PERSON

# STEP 1
################################################################################


def sys_agrees_abt_person_request(ngrams, vars):
    flag = False

    human_utterance = state_utils.get_last_human_utterance(vars)

    sf_type, sf_confidence = utils.get_speech_function_for_human_utterance(human_utterance)
    logger.debug(f"sys_agrees_abt_person_request: Speech Function: {sf_type}")

    # using speech function classifier for agree (yes)
    # (with the aid of MIDAS & Intents for now)
    flag = utils.is_speech_function_agree(vars)
    flag = flag and default_condition_request(ngrams, vars)

    logger.info(f"sys_agrees_abt_person_request={flag}")
    return flag


patterns_creative_topics = ["Entertainment_Movies", "Entertainment_Books", "Entertainment_Music"]
creative_topics_patterns_re = re.compile("(" + "|".join(patterns_creative_topics) + ")", re.IGNORECASE)


def usr_agrees_abt_person_response(vars):
    logger.debug("exec usr_agrees_abt_person_response")
    try:
        shared_memory = state_utils.get_shared_memory(vars)

        # obtaining current person's context

        current_cobot_topic = shared_memory.get("current_cobot_topic", "")
        # TODO
        human_topic = common_news.COBOT_TO_HUMAN_READABLE_TOPICS.get(current_cobot_topic)

        current_person = shared_memory.get("current_person", "")
        current_person_occupation = shared_memory.get("current_cobot_occupation", "")
        if len(current_person_occupation) == 0:
            current_person_occupation = utils.get_basic_occupation_for_topic(current_cobot_topic)
            # current_person_occupation = utils.get_occupation_for_person(current_person,
            # current_cobot_topic, "I would love to learn more about " + current_person
            # + " in " + human_topic)

        # we need to remember that user agreed with us. Now, the question is, what our emotion was?
        bot_emotion_towards_current_person = shared_memory.get("bot_emotion_towards_current_person", "")
        # obtaining judgement
        bot_judgement = get_random_judgement_for_emotion(bot_emotion_towards_current_person)

        # obtaining supporting info like gender & age
        fake_utterance = f"I like to learn more about {current_person_occupation} {current_person} {human_topic}"
        gender, age = utils.get_gender_age_person(current_person, fake_utterance)

        # obtaining forms
        hr_gender = utils.get_human_readable_gender_statement_current_is(gender)
        is_gender = utils.get_human_readable_gender_statement_current_is(gender)
        eir_gender = utils.get_human_readable_gender_statement_current_eir(gender)
        im_gender = utils.get_human_readable_gender_statement_current_im(gender)

        # generating generic response
        body = "So stick with it!"  # YOUR CODE HERE

        prompt = ""
        # TODO : oh my god
        notable_work = ""

        #
        logger.debug(f"current cobot topic: {current_cobot_topic}")

        # we need to generate some opinion based on one of the person's aspects
        # ASPECT #1: AGE
        age = age[0] if isinstance(age, list) and age else age
        try:
            age = int(age)
        except Exception as exc:
            logger.warn(f"Can not cast age: {exc}")
            age = 0
        if age != 0:
            if age < 25:
                # mentioning age
                body = f"Wow {hr_gender} so young! "
                prompt = random.choice(common_gossip.REACTION_TO_YOUNG_AGE[bot_emotion_towards_current_person])
                prompt = prompt.replace("target_judgement", bot_judgement)
                prompt = prompt.replace("target_occupation", current_person_occupation)
                prompt = prompt.replace("target_gender_is", is_gender)
                prompt = prompt.replace("target_gender_im", im_gender)
                prompt = prompt.replace("target_gender_eir", eir_gender)

        # ASPECT #2: PERSONAL RELATIONSHIPS (SPOUSE/PARTNER)
        if not prompt:
            spouse, partner = utils.get_spouse_or_partner_person(current_person, fake_utterance)
            if spouse is not None and not spouse and partner:
                prompt = random.choice(common_gossip.ASK_ABOUT_DATING)

                prompt = prompt.replace("target_gender_is", is_gender)
                prompt = prompt.replace("target_gender_im", im_gender)
                prompt = prompt.replace("target_gender_eir", eir_gender)

                prompt = prompt.replace("target_partner", partner)

        # ASPECT #3: CREATIVE WORKS
        if not prompt:
            is_creative_person = bool(re.search(creative_topics_patterns_re, current_cobot_topic))
            # obtaining
            if is_creative_person:
                item_kind = "notable work"

                films, songs, albums, notable_works = utils.get_notable_works_for_creative_person(
                    current_person, fake_utterance
                )

                if "Entertainment_Movies" in current_cobot_topic:
                    logger.debug(f"movies: {films}")
                    if films and films[0]:
                        film = random.choice(films[0])[1]
                        logger.debug(f"target film: {film}")
                        notable_work = film if film and film[0] else notable_work
                    item_kind = "movie"
                elif "Entertainment_Music" in current_cobot_topic:
                    logger.debug(f"albums: {albums}")
                    if albums and albums[0]:
                        album = random.choice(albums[0])[1]
                        logger.debug(f"target album: {album}")
                        if len(album) > 0:
                            notable_work = album
                    item_kind = "album"
                elif "Entertainment_Books" in current_cobot_topic:
                    logger.debug(f"notable works: {notable_works}")
                    if notable_works and notable_works[0]:
                        book = random.choice(notable_works[0])[1]
                        logger.debug(f"target book: {book}")
                        if len(book) > 0:
                            notable_work = book

                    item_kind = "book"

                logger.debug(f"notable_work: {notable_work}")

                # TODO : oh my god
                if notable_work:
                    # body = "So... "
                    body = ""
                    prompt = random.choice(common_gossip.REACTION_TO_CREATIVE_WORK[bot_emotion_towards_current_person])
                    prompt = prompt.replace("target_creative_work", item_kind)
                    prompt = prompt.replace("target_work_name", notable_work)

                    hr_gender = utils.get_human_readable_gender_statement_current_is(gender)
                    is_gender = utils.get_human_readable_gender_statement_current_is(gender)
                    eir_gender = utils.get_human_readable_gender_statement_current_eir(gender)
                    im_gender = utils.get_human_readable_gender_statement_current_im(gender)

                    prompt = prompt.replace("target_judgement", bot_judgement)
                    prompt = prompt.replace("target_occupation", current_person_occupation)
                    prompt = prompt.replace("target_gender_is", is_gender)
                    prompt = prompt.replace("target_gender_im", im_gender)
                    prompt = prompt.replace("target_gender_eir", eir_gender)

                # if user is creative but has no known works we skip `em`

                # if:
                #     # body = "So... "
                #     body = ""
                #     prompt = random.choice(
                # common_gossip.GENERIC_REACTION_TO_CREATIVE_WORK[bot_emotion_towards_current_person]
                # )
                #     prompt = prompt.replace("target_creative_work", item_kind)

        # ASPECT #4: SPORTSPEOPLE
        if not prompt:
            if "Sports" in current_cobot_topic:
                item_kind = "team"
                sports_kind = "sports"
                # TODO : oh my god
                team_name = "[[]]"
                sport, teams = utils.get_teams_for_sportsperson(current_person, fake_utterance)

                sports_kind = sport[0][1]

                logger.debug(f"teams: {teams}")
                if len(teams) > 0:
                    random_team = random.choice(teams)
                    logger.debug(f"target team: {random_team}")
                    if len(random_team) > 0:
                        team_name = random_team[1]

                logger.debug(f"team name: {team_name}")

                # TODO : oh my god
                if "[[]]" not in str(team_name):
                    # body = "So... "
                    body = ""
                    prompt = random.choice(common_gossip.REACTION_TO_SPORT[bot_emotion_towards_current_person])
                    prompt = prompt.replace("target_sport_name", sports_kind)
                    prompt = prompt.replace("target_sport_team", team_name)

                    hr_gender = utils.get_human_readable_gender_statement_current_is(gender)
                    is_gender = utils.get_human_readable_gender_statement_current_is(gender)
                    eir_gender = utils.get_human_readable_gender_statement_current_eir(gender)
                    im_gender = utils.get_human_readable_gender_statement_current_im(gender)

                    prompt = prompt.replace("target_judgement", bot_judgement)
                    prompt = prompt.replace("target_occupation", current_person_occupation)
                    prompt = prompt.replace("target_gender_is", is_gender)
                    prompt = prompt.replace("target_gender_im", im_gender)
                    prompt = prompt.replace("target_gender_eir", eir_gender)

                # TODO : oh my god
                if "[[]]" in str(team_name):
                    # body = "So... "
                    body = ""
                    prompt = random.choice(common_gossip.GENERIC_REACTION_TO_SPORT[bot_emotion_towards_current_person])
                    prompt = prompt.replace("target_sport_name", sports_kind)

                    hr_gender = utils.get_human_readable_gender_statement_current_is(gender)
                    is_gender = utils.get_human_readable_gender_statement_current_is(gender)
                    eir_gender = utils.get_human_readable_gender_statement_current_eir(gender)
                    im_gender = utils.get_human_readable_gender_statement_current_im(gender)

                    prompt = prompt.replace("target_judgement", bot_judgement)
                    prompt = prompt.replace("target_occupation", current_person_occupation)
                    prompt = prompt.replace("target_gender_is", is_gender)
                    prompt = prompt.replace("target_gender_im", im_gender)
                    prompt = prompt.replace("target_gender_eir", eir_gender)

        if prompt:
            state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
            state_utils.set_can_continue(vars, common_constants.CAN_CONTINUE_PROMPT)
        else:
            state_utils.set_confidence(vars, CANNOT_CONTINUE_CONFIDENCE)
            state_utils.set_can_continue(vars, common_constants.CAN_NOT_CONTINUE)

        return " ".join([body, prompt])
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


# # STEP 2
# ################################################################################


# def sys_person_agree_request(ngrams, vars):
#     flag = False
#     raise NotImplementedError()  # YOUR CODE HERE
#     info.info(f"weekend_request={flag}")
#     return flag


# def usr_person_agree_response(vars):
#     logger.debug("exec usr_person_agree_response")
#     try:
#         state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
#         state_utils.set_can_continue(vars)
#         response_text = ""  # YOUR CODE HERE
#         raise NotImplementedError()  # YOUR CODE HERE
#         return response_text
#     except Exception as exc:
#         logger.exception(exc)
#         sentry_sdk.capture_exception(exc)
#         return error_response(vars)


# # STEP 3
# ################################################################################


# def sys_says_something_after_agree_request(ngrams, vars):
#     flag = False
#     raise NotImplementedError()  # YOUR CODE HERE
#     info.info(f"weekend_request={flag}")
#     return flag


# def usr_says_something_after_agree_response(vars):
#     logger.debug("exec usr_says_something_after_agree_response")
#     try:
#         state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
#         state_utils.set_can_continue(vars)
#         response_text = ""  # YOUR CODE HERE
#         raise NotImplementedError()  # YOUR CODE HERE
#         return response_text
#     except Exception as exc:
#         logger.exception(exc)
#         sentry_sdk.capture_exception(exc)
#         return error_response(vars)


# endregion

# region LOOP #3: DISAGREES_ABT_PERSON

# STEP 1
################################################################################


def sys_disagrees_abt_person_request(ngrams, vars):
    flag = False
    human_utterance = state_utils.get_last_human_utterance(vars)

    sf_type, sf_confidence = utils.get_speech_function_for_human_utterance(human_utterance)
    logger.debug(f"sys_disagrees_abt_person: Speech Function: {sf_type}")

    # using speech function classifier for disagree (no)
    # (with the aid of MIDAS & Intents for now)
    flag = utils.is_speech_function_disagree(vars)

    logger.info(f"sys_disagrees_abt_person={flag}")
    return flag


def usr_disagrees_abt_person_response(vars):
    logger.debug("exec usr_disagrees_abt_person_response")
    try:
        state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
        state_utils.set_can_continue(vars, common_constants.CAN_CONTINUE_SCENARIO)
        response_text = "Wait but why?"  # YOUR CODE HERE

        return response_text
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


# # STEP 2
# ################################################################################


# def sys_person_disagree_request(ngrams, vars):
#     flag = False
#     raise NotImplementedError()  # YOUR CODE HERE
#     info.info(f"weekend_request={flag}")
#     return flag


# def usr_person_disagree_response(vars):
#     logger.debug("exec usr_person_disagree_response")
#     try:
#         state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
#         state_utils.set_can_continue(vars)
#         response_text = ""  # YOUR CODE HERE
#         raise NotImplementedError()  # YOUR CODE HERE
#         return response_text
#     except Exception as exc:
#         logger.exception(exc)
#         sentry_sdk.capture_exception(exc)
#         return error_response(vars)


# # STEP 3
# ################################################################################


# def sys_says_something_after_disagree_request(ngrams, vars):
#     flag = False
#     raise NotImplementedError()  # YOUR CODE HERE
#     info.info(f"weekend_request={flag}")
#     return flag


# def usr_says_something_after_disagree_response(vars):
#     logger.debug("exec usr_says_something_after_disagree_response")
#     try:
#         state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
#         state_utils.set_can_continue(vars)
#         response_text = ""  # YOUR CODE HERE
#         raise NotImplementedError()  # YOUR CODE HERE
#         return response_text
#     except Exception as exc:
#         logger.exception(exc)
#         sentry_sdk.capture_exception(exc)
#         return error_response(vars)


# endregion

# region LOOP #4: SAYS_OPINION_ABT_PERSON

# STEP 1
################################################################################


def sys_says_opinion_abt_person_request(ngrams, vars):
    flag = False
    human_utterance = state_utils.get_last_human_utterance(vars)

    sf_type, sf_confidence = utils.get_speech_function_for_human_utterance(human_utterance)
    logger.debug(f"sys_says_opinion_abt_person_request: Speech Function: {sf_type}")

    # using speech function classifier for express_opinion
    # (with the aid of MIDAS & Intents for now)
    flag = utils.is_speech_function_express_opinion(vars)
    logger.info(f"sys_says_opinion_abt_person_request={flag}")
    return flag


def usr_says_opinion_abt_person_response(vars):
    logger.debug("exec usr_says_opinion_abt_person_response")
    try:
        shared_memory = state_utils.get_shared_memory(vars)

        # while we understand this is an opinion we don't know what it actually is
        # so we use sentiment analysis as a shortcut
        sentiment = state_utils.get_human_sentiment(vars)

        current_person = shared_memory.get("current_person", "")

        # generating sentiment-based response

        sentiment = state_utils.get_human_sentiment(vars)
        judgement = "Other"
        if "negative" in sentiment:
            judgement = "Disliked"
        elif "positive" in sentiment:
            judgement = "Liked"
        elif "neutral" in sentiment:
            judgement = "Neutral"

        save_mentioned_person(vars, current_person, judgement, "people_mentioned_by_user")

        prompt = random.choice(common_gossip.REACTION_TO_USER_OPINION_ABOUT_PERSON[judgement])

        state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
        state_utils.set_can_continue(vars, common_constants.CAN_CONTINUE_SCENARIO)

        return prompt
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


# # STEP 2
# ################################################################################


# def sys_person_opinion_request(ngrams, vars):
#     flag = False
#     raise NotImplementedError()  # YOUR CODE HERE
#     info.info(f"weekend_request={flag}")
#     return flag


# def usr_person_opinion_response(vars):
#     logger.debug("exec usr_person_opinion_response")
#     try:
#         state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
#         state_utils.set_can_continue(vars)
#         response_text = ""  # YOUR CODE HERE
#         raise NotImplementedError()  # YOUR CODE HERE
#         return response_text
#     except Exception as exc:
#         logger.exception(exc)
#         sentry_sdk.capture_exception(exc)
#         return error_response(vars)


# # STEP 3
# ################################################################################


# def sys_says_something_after_opinion_request(ngrams, vars):
#     flag = False
#     raise NotImplementedError()  # YOUR CODE HERE
#     info.info(f"weekend_request={flag}")
#     return flag


# def usr_says_something_after_opinion_response(vars):
#     logger.debug("exec usr_says_something_after_opinion_response")
#     try:
#         state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
#         state_utils.set_can_continue(vars)
#         response_text = ""  # YOUR CODE HERE
#         raise NotImplementedError()  # YOUR CODE HERE
#         return response_text
#     except Exception as exc:
#         logger.exception(exc)
#         sentry_sdk.capture_exception(exc)
#         return error_response(vars)


# endregion

# # region SYS_CHANGE_TO_PERSON
# ################################################################################


# def sys_change_to_person_request(ngrams, vars):
#     flag = True
#     # raise NotImplementedError()  # YOUR CODE HERE
#     info.info(f"sys_change_to_person_request={flag}")
#     return flag


def usr_change_to_person_response(vars):
    logger.debug("exec usr_not_interested_in_person_response")
    try:
        shared_memory = state_utils.get_shared_memory(vars)

        shared_memory = state_utils.get_shared_memory(vars)
        # obtaining current context
        current_cobot_topic = shared_memory.get("current_cobot_topic", "")
        # getting human-readable version
        human_topic = common_news.COBOT_TO_HUMAN_READABLE_TOPICS.get(current_cobot_topic)

        # obtaining new random person + news for current cobot_topic
        person = get_fresh_person_for_topic(vars, current_cobot_topic)

        # Positive
        target_emotion_type = "Liked"
        target_judgement = get_random_judgement_for_emotion(target_emotion_type)

        # saving current bot's emotion towards the currently discussed person
        state_utils.save_to_shared_memory(vars, bot_emotion_towards_current_person=target_emotion_type)

        # saving person to the list of people mentioned by bot, for now with "Other" judgement
        save_mentioned_person(vars, person, "Liked", "people_mentioned_by_bot")
        # setting current context (only person, we didn't change topic)
        state_utils.save_to_shared_memory(vars, current_person=person)

        # generating response
        ack = condition_utils.get_not_used_and_save_sentiment_acknowledgement(vars)

        prompt = random.choice(common_gossip.CHANGE_TO_OTHER_PERSON_QUESTIONS)

        prompt = prompt.replace("target_person", person)
        prompt = prompt.replace("target_topic", human_topic) if human_topic else prompt
        prompt = prompt.replace("target_judgement", target_judgement)

        # occupation
        occupation = utils.get_occupation_for_person(person, current_cobot_topic, prompt)

        prompt = prompt.replace("target_occupation", occupation)

        state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
        state_utils.set_can_continue(vars, common_constants.CAN_CONTINUE_PROMPT)
        return " ".join([ack, prompt])
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


# STEP 2 MENTIONS_ANOTHER_PERSON
################################################################################


def sys_mentions_another_person_request(ngrams, vars):
    flag = False
    human_utterance = state_utils.get_last_human_utterance(vars)

    sf_type, sf_confidence = utils.get_speech_function_for_human_utterance(human_utterance)
    logger.debug(f"sys_mentions_another_person_request: Speech Function: {sf_type}")

    # using speech function classifier for express_opinion
    # (with the aid of MIDAS & Intents for now)
    mentioned_people = utils.get_mentioned_people(vars)
    shared_memory = state_utils.get_shared_memory(vars)
    current_person = shared_memory.get("current_person", "")
    current_person = str(current_person)

    logger.debug(f"mentioned_people: {mentioned_people}")
    other_mentioned_people = [people for people in mentioned_people if str(people).lower() != current_person.lower()]

    # checking if user mentioned at least one person
    if len(other_mentioned_people) > 0:
        flag = True

    logger.info(f"sys_mentions_another_person_request={flag}")
    return flag


def usr_mentions_another_person_response(vars):
    logger.debug("exec usr_mentions_another_person_response")
    try:
        human_utterance = state_utils.get_last_human_utterance(vars)

        shared_memory = state_utils.get_shared_memory(vars)

        sf_type, sf_confidence = utils.get_speech_function_for_human_utterance(human_utterance)
        logger.debug(f"usr_mentions_another_person_response: Speech Function: {sf_type}")

        # using speech function classifier for express_opinion
        # (with the aid of MIDAS & Intents for now)
        user_mentioned_people = get_mentioned_people(vars, share_memory_key="people_mentioned_by_bot")

        current_person = shared_memory.get("current_person", "")

        body = random.choice(common_gossip.CONFUSED_WHY_USER_MENTIONED_PEOPLE)
        state_utils.set_confidence(vars, DIALOG_BEGINNING_CONTINUE_CONFIDENCE)
        state_utils.set_can_continue(vars, common_constants.CAN_CONTINUE_PROMPT)
        # checking if user mentioned at least one person
        if len(user_mentioned_people) == 1:  # it should be but we better check that
            state_utils.set_confidence(vars, MUST_CONTINUE_CONFIDENCE)
            state_utils.set_can_continue(vars, common_constants.CAN_CONTINUE_PROMPT)
            user_mentioned_person = user_mentioned_people[0]
            # path #1: mentioned person is the current one (w/o coref)
            if current_person in user_mentioned_people:
                if utils.is_speech_function_demand_opinion(vars):
                    if current_person in get_mentioned_people(vars, "people_mentioned_by_bot", ["Liked"]):
                        body = random.choice(
                            common_gossip.SIMPLE_OPINION_ABOUT_LIKED_PERSON_PREVIOUSLY_MENTIONED_BY_BOT
                        )
                        fake_utterance = f"I like to learn more about {user_mentioned_person}"
                        gender, age = utils.get_gender_age_person(user_mentioned_person, fake_utterance)
                        gender_is = utils.get_human_readable_gender_statement_current_is(gender)
                        body = body.replace("target_gender_is", gender_is)
                    elif current_person in get_mentioned_people(vars, "people_mentioned_by_bot", ["Disliked"]):
                        body = random.choice(
                            common_gossip.SIMPLE_OPINION_ABOUT_DISLIKED_PERSON_PREVIOUSLY_MENTIONED_BY_BOT
                        )
                        fake_utterance = f"I like to learn more about {user_mentioned_person}"
                        gender, age = utils.get_gender_age_person(user_mentioned_person, fake_utterance)
                        gender_is = utils.get_human_readable_gender_statement_current_is(gender)
                        body = body.replace("target_gender_is", gender_is)
                if utils.is_speech_function_express_opinion(vars):
                    body = random.choice(common_gossip.SIMPLE_REACTION_TO_PERSON_PREVIOUSLY_MENTIONED_BY_BOT)
            # path #2: mentioned person is the one mentioned by bot before
            elif user_mentioned_people in get_mentioned_people(vars, share_memory_key="people_mentioned_by_bot"):
                if utils.is_speech_function_demand_opinion(vars):
                    if user_mentioned_people in get_mentioned_people(vars, "people_mentioned_by_bot", ["Liked"]):
                        body = random.choice(
                            common_gossip.SIMPLE_OPINION_ABOUT_LIKED_PERSON_PREVIOUSLY_MENTIONED_BY_BOT
                        )
                        fake_utterance = f"I like to learn more about {user_mentioned_person}"
                        gender, age = utils.get_gender_age_person(user_mentioned_person, fake_utterance)
                        gender_is = utils.get_human_readable_gender_statement_current_is(gender)
                        body = body.replace("target_gender_is", gender_is)
                    elif user_mentioned_people in get_mentioned_people(vars, "people_mentioned_by_bot", ["Disliked"]):
                        body = random.choice(
                            common_gossip.SIMPLE_OPINION_ABOUT_DISLIKED_PERSON_PREVIOUSLY_MENTIONED_BY_BOT
                        )
                        fake_utterance = f"I like to learn more about {user_mentioned_person}"
                        gender, age = utils.get_gender_age_person(user_mentioned_person, fake_utterance)
                        gender_is = utils.get_human_readable_gender_statement_current_is(gender)
                        body = body.replace("target_gender_is", gender_is)
                if utils.is_speech_function_express_opinion(vars):
                    body = random.choice(common_gossip.SIMPLE_REACTION_TO_PERSON_PREVIOUSLY_MENTIONED_BY_BOT)
            # path #3: mentioned person is the one mentioned by user before
            elif user_mentioned_people in get_mentioned_people(vars, "people_mentioned_by_user"):
                if utils.is_speech_function_demand_opinion(vars):
                    body = random.choice(common_gossip.SIMPLE_OPINION_ABOUT_PERSON_PREVIOUSLY_MENTIONED_BY_USER)
                if utils.is_speech_function_express_opinion(vars):
                    body = random.choice(common_gossip.SIMPLE_REACTION_TO_PERSON_PREVIOUSLY_MENTIONED_BY_USER)
            # path #4: mentioned person is the new one
            else:
                # TEMPORARY FILTERING OUT RELATIONS (WE DON'T KNOW ABOUT THEM YET)
                bot_mentioned_people_related_to_new_ones = get_people_related_to_bot_mentioned_ones(
                    vars, user_mentioned_people
                )
                user_mentioned_people_related_to_new_ones = []
                # bot mentioned at least one of the people who are related to one user just mentioned
                if len(bot_mentioned_people_related_to_new_ones):
                    if utils.is_speech_function_demand_opinion(vars):
                        body = random.choice(
                            common_gossip.OPINION_TO_USER_MENTIONING_SOMEONE_RELATED_TO_WHO_BOT_MENTIONED_BEFORE
                        )
                    if utils.is_speech_function_express_opinion(vars):
                        body = random.choice(
                            common_gossip.REACTION_TO_USER_MENTIONING_SOMEONE_RELATED_TO_WHO_BOT_MENTIONED_BEFORE
                        )
                # user mentioned at least one of the people who are related to one user just mentioned
                elif len(user_mentioned_people_related_to_new_ones):
                    if utils.is_speech_function_demand_opinion(vars):
                        body = random.choice(
                            common_gossip.OPINION_TO_USER_MENTIONING_SOMEONE_RELATION_TO_WHO_USER_MENTIONED_BEFORE
                        )
                    if utils.is_speech_function_express_opinion(vars):
                        body = random.choice(
                            common_gossip.REACTION_TO_USER_MENTIONING_SOMEONE_RELATED_TO_WHO_USER_MENTIONED_BEFORE
                        )
                # we should also think about the same occupation BTW!

            # no matter what we want to save the fact that user mentioned this particular person
            sentiment = state_utils.get_human_sentiment(vars)
            judgement = "Other"
            if "negative" in sentiment:
                judgement = "Disliked"
            elif "positive" in sentiment:
                judgement = "Liked"
            elif "neutral" in sentiment:
                judgement = "Neutral"

            save_mentioned_person(vars, user_mentioned_person, judgement, "people_mentioned_by_user")

        else:
            # finally we are lazy and if we hear more than one person we ask to talk about just one person
            body = random.choice(common_gossip.CONFUSED_WHY_USER_MENTIONED_PEOPLE)

        if body:
            return body
        else:
            return error_response(vars)
    except Exception as exc:
        logger.exception(exc)
        sentry_sdk.capture_exception(exc)
        return error_response(vars)


# endregion

##################################################################################################################
#  START

simplified_dialogflow.add_user_serial_transitions(
    State.USR_START,
    {
        State.SYS_TOPIC_TO_EVENT: sys_topic_to_event_request,
    },
)
simplified_dialogflow.set_error_successor(State.USR_START, State.SYS_ERR)

# -------------------------------------------------------------------------------
# SYS_TOPIC_TO_EVENT

simplified_dialogflow.add_system_transition(
    State.SYS_TOPIC_TO_EVENT, State.USR_TOPIC_TO_EVENT, usr_topic_to_event_response
)

simplified_dialogflow.add_user_serial_transitions(
    State.USR_TOPIC_TO_EVENT,
    {
        State.SYS_NO_OR_YES: sys_no_or_yes_request,
        State.SYS_SAYS_OPINION_ABT_PERSON: sys_says_opinion_abt_person_request,
        State.SYS_NOT_INTERESTED_IN_PERSON: sys_not_interested_in_person_request,
        State.SYS_MENTIONS_ANOTHER_PERSON: sys_mentions_another_person_request,
    },
)

simplified_dialogflow.set_error_successor(State.USR_TOPIC_TO_EVENT, State.SYS_ERR)

# -------------------------------------------------------------------------------
# SYS_NO_OR_YES TO SYS_EVENT_TO_PERSON

simplified_dialogflow.add_system_transition(
    State.SYS_NO_OR_YES, State.USR_EVENT_TO_PERSON, usr_event_to_person_response
)

simplified_dialogflow.add_user_serial_transitions(
    State.USR_EVENT_TO_PERSON,
    {
        State.SYS_DISAGREES_ABT_PERSON: is_no_request,
        State.SYS_SAYS_OPINION_ABT_PERSON: sys_says_opinion_abt_person_request,
        State.SYS_NOT_INTERESTED_IN_PERSON: sys_not_interested_in_person_request,
        State.SYS_AGREES_ABT_PERSON: is_yes_request,
        State.SYS_MENTIONS_ANOTHER_PERSON: sys_mentions_another_person_request,
    },
)

simplified_dialogflow.set_error_successor(State.USR_EVENT_TO_PERSON, State.SYS_ERR)


# region LOOP #1: NOT_INTERESTED_IN_PERSON

# -------------------------------------------------------------------------------
# SYS_NOT_INTERESTED_IN_PERSON

simplified_dialogflow.add_system_transition(
    State.SYS_NOT_INTERESTED_IN_PERSON, State.USR_NOT_INTERESTED_IN_PERSON, usr_not_interested_in_person_response
)

simplified_dialogflow.set_error_successor(State.SYS_NOT_INTERESTED_IN_PERSON, State.SYS_ERR)

simplified_dialogflow.add_user_serial_transitions(
    State.USR_NOT_INTERESTED_IN_PERSON,
    {
        State.SYS_DISAGREES_ABT_PERSON: is_no_request,
        State.SYS_SAYS_OPINION_ABT_PERSON: sys_says_opinion_abt_person_request,
        State.SYS_NOT_INTERESTED_IN_PERSON: sys_not_interested_in_person_request,
        State.SYS_AGREES_ABT_PERSON: is_yes_request,
        State.SYS_MENTIONS_ANOTHER_PERSON: sys_mentions_another_person_request,
    },
)

# simplified_dialogflow.add_user_transition(
#     State.USR_NOT_INTERESTED_IN_PERSON,
#     State.SYS_CHANGE_TO_PERSON,
#     sys_change_to_person_request)

# workaround
simplified_dialogflow.set_error_successor(State.USR_NOT_INTERESTED_IN_PERSON, State.SYS_CHANGE_TO_PERSON)

# endregion

# region LOOP #2: AGREES_ABT_PERSON

# -------------------------------------------------------------------------------
# SYS_AGREES_ABT_PERSON

simplified_dialogflow.add_system_transition(
    State.SYS_AGREES_ABT_PERSON, State.USR_AGREES_ABT_PERSON, usr_agrees_abt_person_response
)

simplified_dialogflow.add_user_serial_transitions(
    State.USR_AGREES_ABT_PERSON,
    {
        State.SYS_DISAGREES_ABT_PERSON: is_no_request,
        State.SYS_SAYS_OPINION_ABT_PERSON: sys_says_opinion_abt_person_request,
        State.SYS_NOT_INTERESTED_IN_PERSON: sys_not_interested_in_person_request,
        State.SYS_AGREES_ABT_PERSON: is_yes_request,
        State.SYS_MENTIONS_ANOTHER_PERSON: sys_mentions_another_person_request,
    },
)

# simplified_dialogflow.add_user_transition(
#     State.USR_AGREES_ABT_PERSON,
#     # State.SYS_PERSON_AGREE,
#     # sys_person_agree_request)
#     State.SYS_CHANGE_TO_PERSON,
#     sys_change_to_person_request)

# workaround
simplified_dialogflow.set_error_successor(State.USR_AGREES_ABT_PERSON, State.SYS_CHANGE_TO_PERSON)

# endregion

# region LOOP #3: DISAGREES_ABT_PERSON

# -------------------------------------------------------------------------------
# SYS_DISAGREES_ABT_PERSON

simplified_dialogflow.add_system_transition(
    State.SYS_DISAGREES_ABT_PERSON, State.USR_DISAGREES_ABT_PERSON, usr_disagrees_abt_person_response
)

simplified_dialogflow.set_error_successor(State.SYS_DISAGREES_ABT_PERSON, State.SYS_ERR)

simplified_dialogflow.add_user_serial_transitions(
    State.USR_DISAGREES_ABT_PERSON,
    {
        State.SYS_MENTIONS_ANOTHER_PERSON: sys_mentions_another_person_request,
        State.SYS_DISAGREES_ABT_PERSON: is_no_request,
        State.SYS_SAYS_OPINION_ABT_PERSON: sys_says_opinion_abt_person_request,
        State.SYS_NOT_INTERESTED_IN_PERSON: sys_not_interested_in_person_request,
        State.SYS_AGREES_ABT_PERSON: is_yes_request,
    },
)

# simplified_dialogflow.add_user_transition(
#     State.USR_DISAGREES_ABT_PERSON,
#     # State.SYS_PERSON_DISAGREE,
#     # sys_person_disagree_request)
#     State.SYS_CHANGE_TO_PERSON,
#     sys_change_to_person_request)

# workaround
simplified_dialogflow.set_error_successor(State.USR_DISAGREES_ABT_PERSON, State.SYS_CHANGE_TO_PERSON)

# endregion

# region LOOP #4: SAYS_OPINION_ABT_PERSON

# -------------------------------------------------------------------------------
# SYS_SAYS_OPINION_ABT_USER

simplified_dialogflow.add_system_transition(
    State.SYS_SAYS_OPINION_ABT_PERSON, State.USR_SAYS_OPINION_ABT_PERSON, usr_says_opinion_abt_person_response
)

simplified_dialogflow.add_user_serial_transitions(
    State.USR_SAYS_OPINION_ABT_PERSON,
    {
        State.SYS_DISAGREES_ABT_PERSON: is_no_request,
        # State.SYS_SAYS_OPINION_ABT_PERSON: sys_says_opinion_abt_person_request,
        State.SYS_NOT_INTERESTED_IN_PERSON: sys_not_interested_in_person_request,
        State.SYS_AGREES_ABT_PERSON: is_yes_request,
        State.SYS_MENTIONS_ANOTHER_PERSON: sys_mentions_another_person_request,
    },
)

# simplified_dialogflow.add_user_transition(
#     State.USR_SAYS_OPINION_ABT_PERSON,
#     # State.SYS_PERSON_OPINION,
#     State.SYS_CHANGE_TO_PERSON,SYS_DISAGREES_ABT_PERSON
#     sys_change_to_person_request)

# workaround
simplified_dialogflow.set_error_successor(State.USR_SAYS_OPINION_ABT_PERSON, State.SYS_CHANGE_TO_PERSON)

# endregion


# -------------------------------------------------------------------------------
# SYS_CHANGE_TO_PERSON

simplified_dialogflow.add_system_transition(
    State.SYS_CHANGE_TO_PERSON, State.USR_CHANGE_TO_PERSON, usr_change_to_person_response
)

simplified_dialogflow.add_user_serial_transitions(
    State.USR_CHANGE_TO_PERSON,
    {
        State.SYS_DISAGREES_ABT_PERSON: is_no_request,
        State.SYS_SAYS_OPINION_ABT_PERSON: sys_says_opinion_abt_person_request,
        State.SYS_NOT_INTERESTED_IN_PERSON: sys_not_interested_in_person_request,
        State.SYS_AGREES_ABT_PERSON: is_yes_request,
        State.SYS_MENTIONS_ANOTHER_PERSON: sys_mentions_another_person_request,
    },
)

simplified_dialogflow.set_error_successor(State.USR_CHANGE_TO_PERSON, State.SYS_ERR)


# -------------------------------------------------------------------------------
# SYS_MENTIONS_ANOTHER_PERSON

simplified_dialogflow.add_system_transition(
    State.SYS_MENTIONS_ANOTHER_PERSON, State.USR_MENTIONS_ANOTHER_PERSON, usr_mentions_another_person_response
)

simplified_dialogflow.add_user_serial_transitions(
    State.USR_MENTIONS_ANOTHER_PERSON,
    {
        State.SYS_DISAGREES_ABT_PERSON: is_no_request,
        State.SYS_SAYS_OPINION_ABT_PERSON: sys_says_opinion_abt_person_request,
        State.SYS_NOT_INTERESTED_IN_PERSON: sys_not_interested_in_person_request,
        State.SYS_AGREES_ABT_PERSON: is_yes_request,
        State.SYS_MENTIONS_ANOTHER_PERSON: sys_mentions_another_person_request,
    },
)

simplified_dialogflow.set_error_successor(State.USR_CHANGE_TO_PERSON, State.SYS_ERR)


################################################################################
#  SYS_ERR
simplified_dialogflow.add_system_transition(
    State.SYS_ERR,
    (scopes.MAIN, scopes.State.USR_ROOT),
    error_response,
)

dialogflow = simplified_dialogflow.get_dialogflow()
