import asyncio
import re
import logging
from itertools import chain
from typing import Dict, Callable
from common.universal_templates import BOOK_TEMPLATES
from common.movies import movie_skill_was_proposed
from common.books import book_skill_was_proposed
from common.constants import CAN_NOT_CONTINUE, CAN_CONTINUE, MUST_CONTINUE
from common.emotion import detect_emotion
from common.news import is_breaking_news_requested
from common.utils import check_about_death, about_virus, quarantine_end
from common.weather import is_weather_for_homeland_requested
from common.coronavirus import is_staying_home_requested


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)


class RuleBasedSkillSelectorConnector:
    sensitive_topics = {"Politics", "Religion", "Sex_Profanity"}
    # `General_ChatIntent` sensitive in case when `?` in reply
    sensitive_dialogacts = {"Opinion_RequestIntent", "General_ChatIntent"}
    movie_cobot_dialogacts = {
        "Entertainment_Movies",
        "Sports",
        "Entertainment_Music",
        "Entertainment_General"
    }
    movie_cobot_topics = {
        "Movies_TV",
        "Celebrities",
        "Art_Event",
        "Entertainment",
        "Fashion",
        "Games",
        "Music",
        "Sports",
    }
    entertainment_cobot_dialogacts = {
        "Entertainment_Movies",
        "Entertainment_Music",
        "Entertainment_General",
        "Entertainment_Books",
    }
    entertainment_cobot_topics = {
        "Art_Event",
        "Celebrities",
        "Entertainment",
        "Games",
    }
    fashion_cobot_dialogacts = set()
    fashion_cobot_topics = {
        "Fashion",
    }
    science_cobot_dialogacts = {
        "Science_and_Technology",
        "Entertainment_Books",
    }
    science_cobot_topics = {
        "Literature",
        "Math",
        "SciTech",
    }
    science_cobot_dialogacts = {
        "Science_and_Technology",
        "Entertainment_Books",
    }
    science_cobot_topics = {
        "Literature",
        "Math",
        "SciTech",
    }
    # politic_cobot_dialogacts = {
    #     "Politics",
    # }
    # politic_cobot_topics = {
    #     "Politics",
    # }
    sport_cobot_dialogacts = {
        "Sports",
    }
    sport_cobot_topics = {
        "Sports",
    }
    animals_cobot_topics = {
        "Pets_Animals",
    }
    books_cobot_dialogacts = {"Entertainment_General", "Entertainment_Books"}
    books_cobot_topics = {"Entertainment", "Literature"}
    news_cobot_topics = {"News"}
    about_movie_words = re.compile(r"(movie|film|picture|series|tv[ -]?show|reality[ -]?show|netflix|\btv\b|"
                                   r"comedy|comedies|thriller|animation|anime|talk[ -]?show|cartoon|drama|"
                                   r"fantasy)")

    async def send(self, payload: Dict, callback: Callable):
        dialog = payload['payload']['states_batch'][0]

        skills_for_uttr = []
        reply = dialog["utterances"][-1]["text"].replace("'", " '").lower()
        # tokens = reply.split()

        # TODO: opinion_request/yes/no response
        intent_detected = any(
            [
                v["detected"] == 1
                for k, v in dialog["utterances"][-1]["annotations"]["intent_catcher"].items()
                if k
                not in {"opinion_request", "yes", "no", "tell_me_more", "doing_well", "weather_forecast_intent",
                        "topic_switching", "lets_chat_about", "stupid", "tell_me_a_story"}
            ]
        )

        ner_detected = len(list(chain.from_iterable(dialog["utterances"][-1]["annotations"]["ner"]))) > 0
        tell_me_a_story_detected = dialog["utterances"][-1]["annotations"]["intent_catcher"].get("tell_me_a_story", {
        }).get("detected", 0)

        cobot_topics = set(dialog["utterances"][-1]["annotations"]["cobot_topics"]["text"])
        sensitive_topics_detected = any([t in self.sensitive_topics for t in cobot_topics])
        cobot_dialogacts = dialog["utterances"][-1]["annotations"]["cobot_dialogact"]["intents"]
        cobot_dialogact_topics = set(dialog["utterances"][-1]["annotations"]["cobot_dialogact"]["topics"])
        sensitive_dialogacts_detected = any(
            [(t in self.sensitive_dialogacts and "?" in reply) for t in cobot_dialogacts]
        )

        blist_topics_detected = dialog["utterances"][-1]["annotations"]["blacklisted_words"]["restricted_topics"]

        about_movies = (self.movie_cobot_dialogacts & cobot_dialogact_topics) | (self.movie_cobot_topics & cobot_topics)
        about_music = ("Entertainment_Music" in cobot_dialogact_topics) | ("Music" in cobot_topics)
        about_books = (self.books_cobot_dialogacts & cobot_dialogact_topics) | (self.books_cobot_topics & cobot_topics)
        #  topicalchat_tfidf_retrieval
        about_entertainments = (self.entertainment_cobot_dialogacts & cobot_dialogact_topics) | (
            self.entertainment_cobot_topics & cobot_topics
        )
        about_fashions = (self.fashion_cobot_dialogacts & cobot_dialogact_topics) | \
            (self.fashion_cobot_topics & cobot_topics)
        # about_politics = (politic_cobot_dialogacts & cobot_dialogact_topics) | (sport_cobot_topics & cobot_topics)
        about_science_technology = (self.science_cobot_dialogacts & cobot_dialogact_topics) | (
            self.science_cobot_topics & cobot_topics
        )
        about_sports = (self.sport_cobot_dialogacts & cobot_dialogact_topics) | (self.sport_cobot_topics & cobot_topics)
        about_animals = self.animals_cobot_topics & cobot_topics

        prev_user_uttr_hyp = []
        prev_bot_uttr = {}

        if len(dialog["human_utterances"]) > 1:
            prev_user_uttr_hyp = dialog["human_utterances"][-2]["hypotheses"]

        if dialog['bot_utterances']:
            prev_bot_uttr = dialog["bot_utterances"][-1]
        prev_active_skill = prev_bot_uttr.get("active_skill", "")

        weather_city_slot_requested = any(
            [
                hyp.get("weather_forecast_interaction_city_slot_requested", False)
                for hyp in prev_user_uttr_hyp
                if hyp["skill_name"] == "weather_skill"
            ]
        )

        about_weather = dialog["utterances"][-1]["annotations"]["intent_catcher"].get(
            "weather_forecast_intent", {}
        ).get("detected", False) or (
            prev_bot_uttr.get("active_skill", "") == "weather_skill" and weather_city_slot_requested
        )
        about_weather = about_weather or is_weather_for_homeland_requested(prev_bot_uttr, dialog['utterances'][-1])
        news_re_expr = re.compile(r"(news|(what is|what's)( the)? new|something new)")
        about_news = (self.news_cobot_topics & cobot_topics) or re.search(
            news_re_expr, reply
        )
        about_news = about_news or is_breaking_news_requested(prev_bot_uttr, dialog['utterances'][-1])
        enable_coronavirus = any([function(dialog['utterances'][-1]['text'])
                                  for function in [about_virus, quarantine_end, check_about_death]])

        enable_coronavirus = enable_coronavirus or is_staying_home_requested(prev_bot_uttr, dialog['utterances'][-1])
        about_movies = (about_movies or movie_skill_was_proposed(prev_bot_uttr) or re.search(
            self.about_movie_words, prev_bot_uttr.get("text", "").lower()))
        about_books = about_books or book_skill_was_proposed(prev_bot_uttr)

        emotions = dialog['utterances'][-1]['annotations']['emotion_classification']['text']
        if "/new_persona" in dialog["utterances"][-1]["text"]:
            # process /new_persona command
            skills_for_uttr.append("personality_catcher")  # TODO: rm crutch of personality_catcher
        elif intent_detected:
            # process intent with corresponding IntentResponder
            skills_for_uttr.append("intent_responder")
        elif blist_topics_detected or (sensitive_topics_detected and sensitive_dialogacts_detected):
            # process user utterance with sensitive content, "safe mode"
            skills_for_uttr.append("program_y_dangerous")
            skills_for_uttr.append("cobotqa")
            skills_for_uttr.append("meta_script_skill")
            skills_for_uttr.append("personal_info_skill")
            if about_news:
                skills_for_uttr.append("news_api_skill")
        else:
            # process regular utterances
            skills_for_uttr.append("program_y")
            skills_for_uttr.append("program_y_wide")
            skills_for_uttr.append("cobotqa")
            skills_for_uttr.append("christmas_new_year_skill")
            skills_for_uttr.append("superbowl_skill")
            skills_for_uttr.append("oscar_skill")
            skills_for_uttr.append("valentines_day_skill")
            skills_for_uttr.append("personal_info_skill")
            skills_for_uttr.append("meta_script_skill")

            if ner_detected:
                skills_for_uttr.append("reddit_ner_skill")

            if len(dialog["human_utterances"]) >= 3:
                # can answer on 3-th user response
                skills_for_uttr.append("convert_reddit")
            if len(dialog["utterances"]) > 7:
                skills_for_uttr.append("alice")
                skills_for_uttr.append("tfidf_retrieval")
                # Disable topicalchat_convert_retrieval v8.7.0
                # skills_for_uttr.append("topicalchat_convert_retrieval")

            if prev_bot_uttr.get("active_skill", "") in ["dummy_skill", "dummy_skill_dialog"] and \
                    len(dialog["utterances"]) > 4:
                skills_for_uttr.append("dummy_skill_dialog")

            # thematic skills
            if about_movies or prev_active_skill == 'movie_skill':
                skills_for_uttr.append("movie_skill")
                skills_for_uttr.append("movie_tfidf_retrieval")
            if enable_coronavirus or prev_active_skill == 'coronavirus_skill':
                skills_for_uttr.append("coronavirus_skill")
            if about_music and len(dialog["utterances"]) > 2:
                skills_for_uttr.append("music_tfidf_retrieval")
            met_book_template = False
            if len(dialog['utterances']) >= 2:
                met_book_template = any([j.lower() in dialog['utterances'][-2]['text'].lower()
                                        for j in BOOK_TEMPLATES])
            if about_books or prev_active_skill == 'book_skill' or met_book_template:
                skills_for_uttr.append("book_skill")
                skills_for_uttr.append("book_tfidf_retrieval")

            if about_weather:
                skills_for_uttr.append("weather_skill")

            if about_entertainments and len(dialog["utterances"]) > 2:
                skills_for_uttr.append("entertainment_tfidf_retrieval")

            if about_fashions and len(dialog["utterances"]) > 2:
                skills_for_uttr.append("fashion_tfidf_retrieval")

            # if about_politics and len(dialog["utterances"]) > 2:
            #     skills_for_uttr.append("politics_tfidf_retrieval")

            if about_science_technology and len(dialog["utterances"]) > 2:
                skills_for_uttr.append("science_technology_tfidf_retrieval")

            if about_sports and len(dialog["utterances"]) > 2:
                skills_for_uttr.append("sport_tfidf_retrieval")

            if about_animals and len(dialog["utterances"]) > 2:
                skills_for_uttr.append("animals_tfidf_retrieval")

            if about_news:
                skills_for_uttr.append("news_api_skill")

            emo_prob_threshold = 0.9  # to check if any emotion has at least this prob
            for emotion, prob in emotions.items():
                if prob == max(emotions.values()):
                    found_emotion, found_prob = emotion, prob
            cond1 = found_emotion != 'neutral' and found_prob > emo_prob_threshold
            should_run_emotion = cond1 or detect_emotion(prev_bot_uttr, dialog['utterances'][-1])
            if should_run_emotion or "how are you?" in prev_bot_uttr.get("text", "").lower():
                skills_for_uttr.append('emotion_skill')

            for hyp in prev_user_uttr_hyp:
                # here we just forcibly add skills which return `can_continue` and it's not `no`
                if hyp.get("can_continue", CAN_NOT_CONTINUE) in {CAN_CONTINUE, MUST_CONTINUE}:
                    skills_for_uttr.append(hyp["skill_name"])

            if len(dialog["utterances"]) > 1:
                # Use only misheard asr skill if asr is not confident and skip it for greeting
                if dialog["utterances"][-1]["annotations"]["asr"]["asr_confidence"] == "very_low":
                    skills_for_uttr = ["misheard_asr"]

            if tell_me_a_story_detected or prev_active_skill == 'short_story_skill':
                # if it's detected - only telling story
                skills_for_uttr = ["short_story_skill"]
        # always add dummy_skill
        skills_for_uttr.append("dummy_skill")
        #  no convert when about coronavirus
        if 'coronavirus_skill' in skills_for_uttr and 'convert_reddit' in skills_for_uttr:
            skills_for_uttr.remove('convert_reddit')

        # (yura): do we really want to always turn small_talk_skill?
        if len(dialog["utterances"]) > 14:
            skills_for_uttr.append("small_talk_skill")

        if "/alexa_" in dialog["utterances"][-1]["text"]:
            skills_for_uttr = ["alexa_handler"]
        asyncio.create_task(callback(
            task_id=payload['task_id'],
            response=list(set(skills_for_uttr))
        ))
