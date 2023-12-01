import logging
from copy import deepcopy

from common.constants import CAN_NOT_CONTINUE
from common.skill_selector_utils_and_constants import DEFAULT_SKILLS


logger = logging.getLogger(__name__)

# this is a list of skills which are not one-lines
ACTIVE_SKILLS = [
    "dff_book_skill",
    "christmas_new_year_skill",
    "dff_coronavirus_skill",
    "dummy_skill_dialog",
    "emotion_skill",
    "game_cooperative_skill",
    "meta_script_skill",
    "dff_movie_skill",
    "news_api_skill",
    "oscar_skill",
    "personal_info_skill",
    "reddit_ner_skill",
    "short_story_skill",
    "superbowl_skill",
    "valentines_dat_skill",
    "dff_weather_skill",
    "wikidata_dial_skill",
    "comet_dialog_skill",
    "dff_animals_skill",
    "dff_food_skill",
    "dff_music_skill",
    "dff_sport_skill",
    "dff_travel_skill",
    "dff_bot_persona_skill",
    "dff_gaming_skill",
    "dff_science_skill",
    "dff_gossip_skill",
    "small_talk_skill",
    "dff_wiki_skill",
    "dff_art_skill",
    "friendship_skill",
    "dff_friendship_skill",
]
UNPREDICTABLE_SKILLS = [
    "convert_reddit",
    "knowledge_grounding_skill",
    "dff_generative_skill",
    "dialogpt",
    "dialogpt_persona_based",
    "seq2seq_persona_based",
]
CAN_NOT_BE_DISLIKED_SKILLS = ["meta_script_skill", "personal_info_skill"]
NOT_ADD_PROMPT_SKILLS = ["alexa_handler", "dff_intent_responder_skill", "misheard_asr", "dff_program_y_dangerous_skill"]

COMPLETELY_CHANGING_THE_SUBJECT_PHRASES = [
    "Completely changing the subject,",
    "This has nothing to do with what we were talking about, but",
    "Not to change the subject, but",
    "Changing gears a little bit,",
    "Changing the topic slightly,",
    "Totally unrelated,",
]

CHANGE_TOPIC_SUBJECT = [
    "Speaking of SUBJECT,",
    "Talking about SUBJECT,",
    "Let's talk about SUBJECT,",
    "I feel we need to discuss SUBJECT,",
    "I wanted to talk with you about SUBJECT,",
    "I wanted to tell you about SUBJECT,",
]

BY_THE_WAY = [
    "By the way,",
    "Anyway,",
    "Oh, before I forget,",
    "I wanted to mention that,",
]


def prioritize_scripted_hypotheses(hypotheses):
    # identify if we have any scripted hypotheses
    if_scripts_available = False
    for hyp in hypotheses:
        if hyp.get("can_continue", CAN_NOT_CONTINUE) != CAN_NOT_CONTINUE:
            if_scripts_available = True
            logger.info("Scripted hypotheses found. Prioritize scripted hypotheses.")
            break

    if if_scripts_available:
        # if we have scripted hypotheses, leave only scripted hypotheses and from default skills
        new_hypotheses = []
        for hyp in hypotheses:
            if hyp["skill_name"] in DEFAULT_SKILLS or hyp.get("can_continue", CAN_NOT_CONTINUE) != CAN_NOT_CONTINUE:
                new_hypotheses.append(deepcopy(hyp))
                continue
            else:
                logger.info(f"Unscripted hypothesis by {hyp['skill_name']} was dropped")
        return new_hypotheses
    else:
        return hypotheses
