"""
This module consolidates possible phrases that links to specific skill.
Also it contains +link_to+ function that returns phrase to link to specific skill
"""
import json
import pathlib
from copy import deepcopy
from random import choice, choices

import common.news as news
import common.books as books
import common.movies as movies
import common.emotion as emotion
# import common.weather as weather
import common.personal_info as personal_info
import common.game_cooperative_skill as game_cooperative_skill
import common.travel as dff_travel_skill
# import common.celebrities as dff_celebrity_skill
import common.gossip as dff_gossip_skill
import common.sport as dff_sport_skill
import common.animals as dff_animals_skill
import common.food as dff_food_skill
import common.music as dff_music_skill
from common.utils import get_not_used_template
from common.response_selection import COMPLETELY_CHANGING_THE_SUBJECT_PHRASES, CHANGE_TOPIC_SUBJECT, BY_THE_WAY
# Each common skill module should define +skill_trigger_phrases()+ function
# that contains all phrases to trigger specific skill

# removing per #99
# 'book_skill': set(books.skill_trigger_phrases()),

skills_phrases_map = {
    'news_api_skill': set(news.skill_trigger_phrases()),
    'movie_skill': set(movies.skill_trigger_phrases()),
    'book_skill': set(books.skill_trigger_phrases()),
    'emotion_skill': set(emotion.skill_trigger_phrases()),
    # 'weather_skill': set(weather.skill_trigger_phrases()),
    'personal_info_skill': set(personal_info.skill_trigger_phrases()),
    'game_cooperative_skill': set(game_cooperative_skill.skill_trigger_phrases()),
    # TODO: Add smalltalk skill phrases that is not identical to meta_script_skill
    'dff_travel_skill': set(dff_travel_skill.skill_trigger_phrases()),
    'dff_animals_skill': set(dff_animals_skill.skill_trigger_phrases()),
    # 'dff_celebrity_skill': set(dff_celebrity_skill.skill_trigger_phrases()),
    'dff_gossip_skill': set(dff_gossip_skill.skill_trigger_phrases()),
    'dff_food_skill': set(dff_food_skill.skill_trigger_phrases()),
    'dff_sport_skill': set(dff_sport_skill.skill_trigger_phrases()),
    'dff_music_skill': set(dff_music_skill.skill_trigger_phrases())
}
# TODO: adding new skill above, add here a conversational topic to the list, it will be used to offer topic in greeting
LIST_OF_SCRIPTED_TOPICS = {
    "news_api_skill": "news",
    "movie_skill": "movies",
    "book_skill": "books",
    "game_cooperative_skill": "games",
    "dff_travel_skill": "travel",
    "dff_animals_skill": "pets",
    "dff_sport_skill": "sport",
    "dff_food_skill": "food",
    "dff_music_skill": "music",
    # "dff_celebrity_skill": "celebrities"
    "dff_gossip_skill": "gossips"
}

SKILLS_FOR_LINKING = set(skills_phrases_map.keys())

LOW_RATED_SKILLS = {
    "emotion_skill",
    # "weather_skill",
    "personal_info_skill",
}
SKILLS_TO_BE_LINKED_EXCEPT_LOW_RATED = set(skills_phrases_map.keys()).difference(LOW_RATED_SKILLS)

# assuming that all skills weights are equal to 1 by default
# it is used to control amount of link_to phrases to specific skills
skills_link_to_weights = {
    'coronavirus_skill': 0.25,
}


def link_to(skills, human_attributes, recent_active_skills=None):
    """
    Returns random skill and phrase from skills_phrases_map.
    Use it to add link to specific skill in your phrase.

    Parameters
    ----------
    skills : array
        Array of skills, used in +skills_phrases_map+
    human_attributes : dict
        where used_links is a dict where:
            Key is skill_name, value is used links phrases.
            Pass it to prevent selecting identical phrases.
            It will try to link_to skills that were not linked before.
    recent_active_skills: list or set of recently used skills not to link to them
    """
    recent_active_skills = [] if recent_active_skills is None else recent_active_skills
    used_links = human_attributes.get("used_links", {})
    disliked_skills = human_attributes.get("disliked_skills", [])

    filtered_phrases_map = deepcopy(skills_phrases_map)
    filtered_skills = set(deepcopy(skills))

    for skill_name, phrases in used_links.items():
        if skill_name in skills_phrases_map:
            filtered_phrases_map[skill_name] = skills_phrases_map[skill_name].difference(set(phrases))
            if len(phrases) > 0:
                filtered_skills.discard(skill_name)

    # all skills were linked before, use original list of skills
    if len(filtered_skills) == 0:
        filtered_skills = set(deepcopy(skills))
    filtered_skills = set(filtered_skills).difference(set(recent_active_skills))
    # all skills among available were active recently, use original list of skills
    if len(filtered_skills) == 0:
        filtered_skills = set(deepcopy(skills))
    filtered_skills = set(filtered_skills).difference(set(disliked_skills))
    # all skills among available are disliked, use original list of skills
    if len(filtered_skills) == 0:
        filtered_skills = set(deepcopy(skills))

    # remove from filtered skills all skills which links all were used before.
    for skill_name, phrases in used_links.items():
        if skill_name in skills_phrases_map:
            if len(filtered_phrases_map[skill_name]) == 0:
                filtered_skills.discard(skill_name)

    if filtered_skills:
        skills_weights = [skills_link_to_weights.get(s, 1.0) for s in filtered_skills]
        random_skill = choices(list(filtered_skills), weights=skills_weights, k=1)[0]
    else:
        # unreal situation if `skills` is not empty list, but let's make it
        skills = list(skills)
        skills_weights = [skills_link_to_weights.get(s, 1.0) for s in skills]
        random_skill = choices(skills, weights=skills_weights, k=1)[0]

    filtered_phrases = list(filtered_phrases_map[random_skill])
    if filtered_phrases:
        random_phrase = choice(filtered_phrases)
    else:
        random_phrase = choice(list(skills_phrases_map[random_skill]))
    return {'phrase': random_phrase, 'skill': random_skill}


def skill_was_linked(skill_name, prev_bot_utt):
    for phrase in skills_phrases_map.get(skill_name, []):
        if phrase.lower() in prev_bot_utt.get('text', '').lower():
            return True
    return False


def get_all_linked_to_skills(prev_bot_utt):
    skills = []
    for skill_name in skills_phrases_map:
        if skill_was_linked(skill_name, prev_bot_utt):
            skills.append(skill_name)

    return skills


prelinkto_connection_phrases_file = pathlib.Path(__file__).resolve().parent / "prelinkto_connection_phrases.json"
PRELINKTO_CONNECTION_PHRASES = json.load(prelinkto_connection_phrases_file.open())


def get_prelinkto_connection(from_skill, to_skill, used_templates):
    skill_pair = sorted([from_skill, to_skill])
    for el in PRELINKTO_CONNECTION_PHRASES:
        if el["skill_pair"] == skill_pair:
            return get_not_used_template(used_templates, el["phrases"])
    return ""


def compose_linkto_with_connection_phrase(skills, human_attributes, recent_active_skills=None, from_skill=None):
    from_skill = "" if from_skill is None else from_skill
    linkto_dict = link_to(skills, human_attributes, recent_active_skills)
    connection = get_prelinkto_connection(from_skill, linkto_dict["skill"],
                                          human_attributes.get("prelinkto_connections", []))
    if not connection:
        connection = get_not_used_template(human_attributes.get("prelinkto_connections", []),
                                           COMPLETELY_CHANGING_THE_SUBJECT_PHRASES)
        result = f"{connection} {linkto_dict['phrase']}"
    else:
        change_topic = choice(CHANGE_TOPIC_SUBJECT).replace(
            "SUBJECT", LIST_OF_SCRIPTED_TOPICS.get(linkto_dict["skill"], "it"))
        result = f"{choice(BY_THE_WAY)} {connection} {change_topic} {linkto_dict['phrase']}"
    return {'phrase': result, 'skill': linkto_dict["skill"], "connection_phrase": connection}
