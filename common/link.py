"""
This module consolidates possible phrases that links to specific skill.
Also it contains +link_to+ function that returns phrase to link to specific skill
"""
import json
import pathlib
from copy import deepcopy
from random import choice, choices

import common.animals as dff_animals_skill
import common.books as books
import common.emotion as emotion
import common.food as dff_food_skill
import common.game_cooperative_skill as game_cooperative_skill
import common.gaming as dff_gaming_skill
import common.movies as movies
import common.music as dff_music_skill
import common.news as news
import common.personal_info as personal_info
import common.science as dff_science_skill
import common.sport as dff_sport_skill
import common.travel as dff_travel_skill
from common.constants import CAN_CONTINUE_SCENARIO, CAN_NOT_CONTINUE, CAN_CONTINUE_PROMPT, MUST_CONTINUE
from common.utils import get_not_used_template
from common.response_selection import COMPLETELY_CHANGING_THE_SUBJECT_PHRASES, CHANGE_TOPIC_SUBJECT, BY_THE_WAY

# Each common skill module should define +skill_trigger_phrases()+ function
# that contains all phrases to trigger specific skill

# removing per #99
# 'book_skill': set(books.skill_trigger_phrases()),

skills_phrases_map = {
    "news_api_skill": set(news.skill_trigger_phrases()),
    "dff_movie_skill": set(movies.skill_trigger_phrases()),
    "dff_book_skill": set(books.skill_trigger_phrases()),
    "emotion_skill": set(emotion.skill_trigger_phrases()),
    "personal_info_skill": set(personal_info.skill_trigger_phrases()),
    "game_cooperative_skill": set(game_cooperative_skill.skill_trigger_phrases()),
    # TODO: Add smalltalk skill phrases that is not identical to meta_script_skill
    "dff_travel_skill": set(dff_travel_skill.skill_trigger_phrases()),
    "dff_animals_skill": set(dff_animals_skill.skill_trigger_phrases()),
    # 'dff_celebrity_skill': set(dff_celebrity_skill.skill_trigger_phrases()),
    # 'dff_gossip_skill': set(dff_gossip_skill.skill_trigger_phrases()),
    "dff_food_skill": set(dff_food_skill.skill_trigger_phrases()),
    "dff_science_skill": set(dff_science_skill.skill_trigger_phrases()),
    "dff_sport_skill": set(dff_sport_skill.skill_trigger_phrases()),
    "dff_music_skill": set(dff_music_skill.skill_trigger_phrases()),
    "dff_gaming_skill": set(dff_gaming_skill.skill_trigger_phrases()),
}
# TODO: adding new skill above, add here a conversational topic to the list, it will be used to offer topic in greeting
LIST_OF_SCRIPTED_TOPICS = {
    "dff_book_skill": "books",
    "news_api_skill": "news",
    "dff_animals_skill": "pets",
    # "dff_celebrity_skill": "celebrities"
    "dff_food_skill": "food",
    "dff_gaming_skill": "games",
    # "dff_gossip_skill": "gossips",
    "dff_movie_skill": "movies",
    "dff_music_skill": "music",
    "dff_science_skill": "science",
    "dff_sport_skill": "sport",
    "dff_travel_skill": "travel",
    "game_cooperative_skill": "games",
}

SKILLS_FOR_LINKING = set(skills_phrases_map.keys())

LOW_RATED_SKILLS = {
    "emotion_skill",
    "personal_info_skill",
}
SKILLS_TO_BE_LINKED_EXCEPT_LOW_RATED = set(skills_phrases_map.keys()).difference(LOW_RATED_SKILLS)

# assuming that all skills weights are equal to 1 by default
# it is used to control amount of link_to phrases to specific skills
skills_link_to_weights = {
    "dff_coronavirus_skill": 0.25,
}

link_to_skill2key_words = {
    "dff_movie_skill": ["movie"],
    "dff_book_skill": ["book"],
    "game_cooperative_skill": ["game"],
    # 'dff_gaming_skill': ["game"],   # TODO: add when will be merged
    "dff_travel_skill": ["travel"],
    "dff_animals_skill": ["animal"],
    "dff_food_skill": ["food"],
    "dff_sport_skill": ["sport"],
    # "dff_gossip_skill": ["gossips"],
    "dff_science_skill": ["science"],
    "dff_music_skill": ["music"],
}

link_to_skill2i_like_to_talk = {
    "dff_book_skill": [
        "I'm choosing what book should I read next. What is the last book you have ever read?",
        "I have just read once again my favourite book. What is the last book you have ever read?",
    ],
    "dff_animals_skill": [
        "I think that pets are a great source of entertainment. Do you have pets at home?",
        "We all know that pets are remarkable for their capacity to love. Do you have pets at home?",
    ],
    "dff_gaming_skill": [
        "Other bots told me that during the pandemic video games became more popular. "
        "What video game do you play these days?",
        "One person I talked to told me that working in game dev is very hard. They toil at nights and weekends until "
        "their product becomes a masterpiece. What was the last game that impressed you?",
    ],
    "dff_gossip_skill": [
        "What really puzzles me about people is this habit of discussing interpersonal relations, be that about "
        "friends or famous people. Speaking of famous people, is there someone whom you're interested in?",
        "I don't usually talk about other people but famous ones often highlight the best and the worst about "
        "humanity. I wonder if there's someone famous you're interested in?",
    ],
    "dff_food_skill": [
        "It is said that the best food in the world comes from your own country. "
        "What are some typical foods from your home country?",
        "It is said that the best food in the world comes from your own country. "
        "If you were to move abroad what would you miss most foodwise?",
        "The world's first breakfast cereal was created in 1863 and needed soaking overnight to be chewable. "
        "What is your typical breakfast?",
    ],
    "dff_movie_skill": [
        "I felt so bored last days, so I've just finished to watch one more series. What TV series you watch?",
        "I feel so sleepy because I watched movies all night. What is the last movie you watched?",
    ],
    "dff_music_skill": [
        "There are so many new songs released every day. I've listened music for all night. So cool! "
        "Liked everything! What music do you listen usually?",
        "I listen to music every day either to calm down or to cheer myself up. "
        "What music do you listen to cheer yourself up?",
        "I listen to music every day either to calm down or to cheer myself up. "
        "What music do you listen to calm down?",
    ],
    "dff_science_skill": [
        "When I start to feel sad, I think about what humanity has achieved and it inspires me. "
        "Do you often think about achievements in science?",
        "Scientists find such beautiful solutions in science. "
        "Are you inspired by the speed with which science is developing?",
    ],
    "dff_sport_skill": [
        "I think that sports are great for toning up the body. What kind of sport do you like to do?",
        "I think that in order for the body to always be healthy, we need to go in for sports. What sport do you do?",
        "I often thought about what kind of sport I would play, so I want to ask you. What kind of sport do you enjoy?",
    ],
    "dff_travel_skill": [
        "I'm choosing the direction for my next digital trip. What country would you like to travel next time?",
        "I've recently stuck on travel web-site. And I’ve read so many interesting travel stories. "
        "What city did you travel last time?",
    ],
    "game_cooperative_skill": [
        "Computer games are fantastic. Their virtual worlds help me to escape my prosaic ordinary life in the cloud. "
        "do you love video games?",
        "Video games are my way to escape and thrive. do you love video games?",
    ],
    "school": [
        "I've never been to school, I've learned everything online. Do you want to talk about school?",
    ],
    "superheroes": [
        "Yesterday I was watching several movies about superheroes. It captured all my imagination. "
        "Would you like to talk about superheroes?",
    ],
}

DFF_WIKI_LINKTO = {
    "space": "Have you ever thought about flights to other planets?",
    "smartphones": "Nowadays it is impossible to imagine world without gadgets. "
    "Do you have an iPhone or Android phone?",
    "bitcoin": "Cryptocurrencies let you buy goods and services, or trade them for profit. "
    "Would you like to know more about bitcoin?",
    "dinosaurs": "Dinosaurs are a group of reptiles that have lived on Earth for about 245 million "
    "years. Are you interested in dinosaurs?",
    "robots": "Robotics technology influences every aspect of work and home. "
    "Would you like to know more about robots?",
    "cars": "Cars are an easy and convenient mean of transportation. Do you have a car?",
    "hiking": "Hiking is one of the most beneficial and healthy hobbies anyone could choose to adopt. "
    "Do you like hiking?",
    "art": "Art is a good way to express feelings. Would you like to talk about art?",
    "drawing": "Drawing gives you a mean to self-reflect and externalize your emotions." "Do you like drawing?",
    "photo": "In our increasingly busy lives it’s difficult to always be in the moment."
    "Taking pictures helps you to hang on to those memories a little longer."
    "Do you like taking photographs?",
    "memes": "Memes are funny artworks we can see on the Internet. Do you like memes?",
    "tiktok": "TikTok is known for its funny lip-syncing videos. Have you shot a video for tiktok?",
    "anime": "Anime is hand-drawn and computer animation originating from Japan. Do you like anime?",
    "friends": "A friend at hand is better than a relative at a distance. Do you have any friends?",
    "love": "I have a lot of friends but as a socialbot I can not fall in love with someone. Although, "
    "I've heard this is an amazing feeling. Are you in relationships with someone?",
    "hobbies": "Success is not the key to happiness. Happiness is the key to success. "
    "If you love what you are doing, you will be successful. Do you have any hobbies?",
    "politics": "I've recently learned how many different political views in our world. "
    "Are you interested in politics?",
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
    return {"phrase": random_phrase, "skill": random_skill}


def skill_was_linked(skill_name, prev_bot_utt):
    for phrase in skills_phrases_map.get(skill_name, []):
        if phrase.lower() in prev_bot_utt.get("text", "").lower():
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

prelinkto_topic_phrases_file = pathlib.Path(__file__).resolve().parent / "prelinkto_topic_phrases.json"
PRELINKTO_TOPIC_PHRASES = json.load(prelinkto_topic_phrases_file.open())


def get_prelinkto_connection(from_skill, to_skill, used_templates):
    skill_pair = sorted([from_skill, to_skill])
    for el in PRELINKTO_CONNECTION_PHRASES:
        if el.get("skill_pair") == skill_pair and el.get("phrases"):
            return get_not_used_template(used_templates, el["phrases"])
    return ""


def get_prelinkto_topic_connection(to_skill, used_templates):
    if to_skill in PRELINKTO_TOPIC_PHRASES:
        return get_not_used_template(used_templates, PRELINKTO_TOPIC_PHRASES[to_skill])
    return ""


def compose_linkto_with_connection_phrase(skills, human_attributes, recent_active_skills=None, from_skill=None):
    from_skill = "" if from_skill is None else from_skill
    linkto_dict = link_to(skills, human_attributes, recent_active_skills)
    connection = get_prelinkto_connection(
        from_skill, linkto_dict["skill"], human_attributes.get("prelinkto_connections", [])
    )
    if not connection:
        connection = get_prelinkto_topic_connection(
            linkto_dict["skill"], human_attributes.get("prelinkto_connections", [])
        )

    if not connection:
        # not found prelinkto connection phrase AND not found prelinkto topic phrase
        connection = get_not_used_template(
            human_attributes.get("prelinkto_connections", []), COMPLETELY_CHANGING_THE_SUBJECT_PHRASES
        )

        result = f"{connection} {linkto_dict['phrase']}"
    else:
        # we have prelinkto connection phrase OR prelinkto topic phrase
        change_topic = choice(CHANGE_TOPIC_SUBJECT).replace(
            "SUBJECT", LIST_OF_SCRIPTED_TOPICS.get(linkto_dict["skill"], "it")
        )
        result = f"{choice(BY_THE_WAY)} {connection} {change_topic} {linkto_dict['phrase']}"
    return {"phrase": result, "skill": linkto_dict["skill"], "connection_phrase": connection}


def get_linked_to_dff_skills(dff_shared_state, current_turn, prev_active_skill):
    """Collect the skill names to turn on (actually this should be the only skill because active skill is the only)
        which were linked to from one dff-skill to another one.

    Returns:
        list of skill names to turn on
    """
    to_skills = []
    for to_skill in dff_shared_state.get("cross_links", {}).keys():
        cross_links = dff_shared_state.get("cross_links", {})[to_skill]
        if (
            cross_links.get(str(current_turn - 1), {}).get("from_service", "") == prev_active_skill
            or cross_links.get(str(current_turn - 2), {}).get("from_service", "") == prev_active_skill
        ):
            to_skills.append(to_skill)

    return to_skills


def get_linked_to_skills(dialog):
    # return skills linked to in the previous bot utterance (of course, it's the only one skill)

    bot_uttr = dialog["bot_utterances"][-1] if len(dialog["bot_utterances"]) else {}
    linked_to_skill_names = get_all_linked_to_skills(bot_uttr)
    prev_active_skill = bot_uttr.get("active_skill", "")

    result = []
    for skill_name in linked_to_skill_names:
        result.append(skill_name)
    result.extend(
        get_linked_to_dff_skills(
            dialog["human"]["attributes"].get("dff_shared_state", {}),
            len(dialog["human_utterances"]),
            prev_active_skill,
        )
    )
    return result


def get_previously_active_skill(dialog):
    # return prev active skill if it returned not `CAN_NOT_CONTINUE`

    prev_user_uttr_hyp = dialog["human_utterances"][-2]["hypotheses"] if len(dialog["human_utterances"]) > 1 else []
    bot_uttr = dialog["bot_utterances"][-1] if len(dialog["bot_utterances"]) else {}
    prev_active_skill = bot_uttr.get("active_skill", "")

    result = []
    for hyp in prev_user_uttr_hyp:
        if hyp.get("can_continue", CAN_NOT_CONTINUE) in {
            CAN_CONTINUE_SCENARIO,
            MUST_CONTINUE,
            CAN_CONTINUE_PROMPT,
        }:
            if hyp["skill_name"] == prev_active_skill:
                result.append(hyp["skill_name"])
    return result
