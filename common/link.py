"""
This module consolidates possible phrases that links to specific skill.
Also it contains +link_to+ function that returns phrase to link to specific skill
"""

from random import choice, choices
import common.news as news
import common.books as books
import common.movies as movies
import common.emotion as emotion
import common.weather as weather
import common.personal_info as personal_info
import common.meta_script as meta_script
import common.game_cooperative_skill as game_cooperative_skill
import common.travel as dff_travel_skill
# import common.celebrities as dff_celebrity_skill
import common.sport as dff_sport_skill
import common.animals as dff_animals_skill
import common.food as dff_food_skill
import common.music as dff_music_skill

# Each common skill module should define +skill_trigger_phrases()+ function
# that contains all phrases to trigger specific skill

# removing per #99
# 'book_skill': set(books.skill_trigger_phrases()),

skills_phrases_map = {
    'news_api_skill': set(news.skill_trigger_phrases()),
    'movie_skill': set(movies.skill_trigger_phrases()),
    'book_skill': set(books.skill_trigger_phrases()),
    'emotion_skill': set(emotion.skill_trigger_phrases()),
    'weather_skill': set(weather.skill_trigger_phrases()),
    'personal_info_skill': set(personal_info.skill_trigger_phrases()),
    'meta_script_skill': set(meta_script.skill_trigger_phrases()),
    # 'short_story_skill': set(short_story.skill_trigger_phrases()),
    'game_cooperative_skill': set(game_cooperative_skill.skill_trigger_phrases()),
    # TODO: Add smalltalk skill phrases that is not identical to meta_script_skill
    'dff_travel_skill': set(dff_travel_skill.skill_trigger_phrases()),
    'dff_animals_skill': set(dff_animals_skill.skill_trigger_phrases()),
    # 'dff_celebrity_skill': set(dff_celebrity_skill.skill_trigger_phrases()),
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
}

SKILLS_FOR_LINKING = set(skills_phrases_map.keys())

LOW_RATED_SKILLS = {"emotion_skill", "weather_skill", "personal_info_skill", "meta_script_skill"}
SKILLS_TO_BE_LINKED_EXCEPT_LOW_RATED = set(skills_phrases_map.keys()).difference(LOW_RATED_SKILLS)

# assuming that all skills weights are equal to 1 by default
# it is used to control amount of link_to phrases to specific skills
skills_link_to_weights = {
    'coronavirus_skill': 0.25,
}


def link_to(skills, human_attributes, recent_active_skills=[]):
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
    used_links = human_attributes.get("used_links", {})
    disliked_skills = human_attributes.get("disliked_skills", [])

    random_skill = ''
    random_phrase = ''
    filtered_phrases_map = dict(skills_phrases_map)
    filtered_skills = set(skills)
    for skill_name, phrases in used_links.items():
        if skill_name in skills_phrases_map:
            filtered_phrases_map[skill_name] = skills_phrases_map[skill_name].difference(set(phrases))
            if len(phrases) > 0:
                filtered_skills.discard(skill_name)

    # all skills were linked before, use original list of skills
    if len(filtered_skills) == 0:
        filtered_skills = skills
    filtered_skills = set(filtered_skills).difference(set(recent_active_skills))
    # all skills among available were active recently, use original list of skills
    if len(filtered_skills) == 0:
        filtered_skills = skills
    filtered_skills = set(filtered_skills).difference(set(disliked_skills))
    # all skills among available are disliked, use original list of skills
    if len(filtered_skills) == 0:
        filtered_skills = skills

    if filtered_skills:
        skills_weights = [skills_link_to_weights.get(s, 1.0) for s in filtered_skills]
        random_skill = choices(list(filtered_skills), weights=skills_weights, k=1)[0]

    filtered_phrases = list(filtered_phrases_map[random_skill])
    if filtered_phrases:
        random_phrase = choice(filtered_phrases)
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
