"""
This module consolidates possible phrases that links to specific skill.
Also it contains +link_to+ function that returns phrase to link to specific skill
"""

from random import choice
import common.news as news
import common.books as books
import common.movies as movies
import common.emotion as emotion
import common.weather as weather
import common.coronavirus as coronavirus


# Each common skill module should define +skill_trigger_phrases()+ function
# that contains all phrases to trigger specific skill
skills_phrases_map = {
    'news_skill': set(news.skill_trigger_phrases()),
    'movie_skill': set(movies.skill_trigger_phrases()),
    'book_skill': set(books.skill_trigger_phrases()),
    'emotion_skill': set(emotion.skill_trigger_phrases()),
    'coronavirus_skill': set(coronavirus.skill_trigger_phrases()),
    'weather_skill': set(weather.skill_trigger_phrases()),
}


def link_to(skills, used_links={}):
    """
    Returns random skill and phrase from skills_phrases_map.
    Use it to add link to specific skill in your phrase.

    Parameters
    ----------
    skills : array
        Array of skills, used in +skills_phrases_map+
    used_links : dict
        Key is skill_name, value is used links phrases.
        Pass it to prevent selecting identical phrases.
    """
    filtered_phrases_map = dict(skills_phrases_map)
    for skill_name, phrases in used_links:
        filtered_phrases_map[skill_name] = skills_phrases_map[skill_name].difference(set(phrases))
    random_skill = choice(skills)
    rand_phrase = choice(list(filtered_phrases_map[random_skill])) or ''
    return {'phrase': rand_phrase, 'skill': random_skill}
