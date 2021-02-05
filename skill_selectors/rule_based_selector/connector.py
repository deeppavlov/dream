import asyncio
import logging
import re
from itertools import chain
from os import getenv
from typing import Dict, Callable

import sentry_sdk

from common.movies import movie_skill_was_proposed
from common.books import book_skill_was_proposed, about_book, QUESTIONS_ABOUT_BOOKS
from common.constants import CAN_NOT_CONTINUE, CAN_CONTINUE, MUST_CONTINUE
from common.emotion import detect_emotion, is_joke_requested
from common.news import is_breaking_news_requested
from common.universal_templates import if_lets_chat_about_topic
from common.utils import service_intents, low_priority_intents, \
    get_topics, get_intents
from common.weather import is_weather_requested
from common.coronavirus import check_about_death, about_virus, quarantine_end, is_staying_home_requested
from common.grounding import what_we_talk_about

sentry_sdk.init(getenv('SENTRY_DSN'))
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
        try:
            dialog = payload['payload']['states_batch'][0]

            skills_for_uttr = []
            user_uttr_text = dialog["human_utterances"][-1]["text"].lower()
            user_uttr_annotations = dialog["human_utterances"][-1]["annotations"]
            lets_chat_about_particular_topic = if_lets_chat_about_topic(user_uttr_text)

            high_priority_intent_detected = any(
                [
                    v["detected"] == 1
                    for k, v in user_uttr_annotations["intent_catcher"].items()
                    if k
                    not in service_intents
                ]
            )
            low_priority_intent_detected = any(
                [
                    v["detected"] == 1
                    for k, v in user_uttr_annotations["intent_catcher"].items()
                    if k in low_priority_intents
                ]
            )

            ner_detected = len(list(chain.from_iterable(user_uttr_annotations["ner"]))) > 0
            logger.info(f"Detected Entities: {ner_detected}")

            cobot_topics = set(get_topics(dialog["human_utterances"][-1], which="cobot_topics"))
            sensitive_topics_detected = any([t in self.sensitive_topics for t in cobot_topics])

            cobot_dialogacts = get_intents(dialog['human_utterances'][-1], which="cobot_dialogact_intents")
            cobot_dialogact_topics = set(get_topics(dialog['human_utterances'][-1], which="cobot_dialogact_topics"))
            # factoid
            factoid_classification = user_uttr_annotations['factoid_classification']['factoid']
            # using factoid
            factoid_prob_threshold = 0.9  # to check if factoid probability has at least this prob
            sensitive_dialogacts_detected = any(
                [(t in self.sensitive_dialogacts and "?" in user_uttr_text) for t in cobot_dialogacts]
            ) or user_uttr_annotations["intent_catcher"].get("opinion_request", {}).get("detected", 0)
            blist_topics_detected = user_uttr_annotations["blacklisted_words"]["restricted_topics"]

            about_movies = (self.movie_cobot_dialogacts & cobot_dialogact_topics)
            about_music = ("Entertainment_Music" in cobot_dialogact_topics) | ("Music" in cobot_topics)
            about_games = ("Games" in cobot_topics and "Entertainment_General" in cobot_dialogact_topics)
            about_books = about_book(dialog["human_utterances"][-1])

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
            about_sports = (self.sport_cobot_dialogacts & cobot_dialogact_topics) | (
                self.sport_cobot_topics & cobot_topics)
            about_animals = self.animals_cobot_topics & cobot_topics

            prev_user_uttr_hyp = []
            prev_bot_uttr = {}

            if len(dialog["human_utterances"]) > 1:
                prev_user_uttr_hyp = dialog["human_utterances"][-2]["hypotheses"]

            if len(dialog['bot_utterances']) > 0:
                prev_bot_uttr = dialog["bot_utterances"][-1]

            prev_active_skill = prev_bot_uttr.get("active_skill", "")

            weather_city_slot_requested = any(
                [
                    hyp.get("weather_forecast_interaction_city_slot_requested", False)
                    for hyp in prev_user_uttr_hyp
                    if hyp["skill_name"] == "weather_skill"
                ]
            )

            about_weather = user_uttr_annotations["intent_catcher"].get(
                "weather_forecast_intent", {}
            ).get("detected", False) or (
                prev_bot_uttr.get("active_skill", "") == "weather_skill" and weather_city_slot_requested
            ) or (lets_chat_about_particular_topic and "weather" in user_uttr_text)
            about_weather = about_weather or is_weather_requested(prev_bot_uttr, dialog['human_utterances'][-1])
            news_re_expr = re.compile(r"(news|(what is|what ?'s)( the)? new|something new)")
            about_news = (self.news_cobot_topics & cobot_topics) or re.search(news_re_expr, user_uttr_text)
            about_news = about_news or is_breaking_news_requested(prev_bot_uttr, dialog['human_utterances'][-1])
            virus_prev = False
            for i in [3, 5]:
                if len(dialog['utterances']) >= i:
                    virus_prev = virus_prev or any([function(dialog['utterances'][-i]['text'])
                                                    for function in [about_virus, quarantine_end]])
            enable_coronavirus_death = check_about_death(user_uttr_text)
            enable_grounding_skill = what_we_talk_about(user_uttr_text)
            enable_coronavirus = any([function(user_uttr_text)
                                      for function in [about_virus, quarantine_end]])
            enable_coronavirus = enable_coronavirus or (enable_coronavirus_death and virus_prev)
            enable_coronavirus = enable_coronavirus or is_staying_home_requested(
                prev_bot_uttr, dialog['human_utterances'][-1])
            about_movies = (about_movies or movie_skill_was_proposed(prev_bot_uttr) or re.search(
                self.about_movie_words, prev_bot_uttr.get("text", "").lower()))
            about_books = about_books or book_skill_was_proposed(prev_bot_uttr)

            emotions = user_uttr_annotations['emotion_classification']['text']
            if "/new_persona" in user_uttr_text:
                # process /new_persona command
                skills_for_uttr.append("personality_catcher")  # TODO: rm crutch of personality_catcher
            elif user_uttr_text == "/get_dialog_id":
                skills_for_uttr.append("dummy_skill")
            elif high_priority_intent_detected:
                # process intent with corresponding IntentResponder
                skills_for_uttr.append("intent_responder")
            elif blist_topics_detected or (sensitive_topics_detected and sensitive_dialogacts_detected):
                # process user utterance with sensitive content, "safe mode"
                skills_for_uttr.append("program_y_dangerous")
                skills_for_uttr.append("cobotqa")
                # skills_for_uttr.append("cobotqa")
                skills_for_uttr.append("meta_script_skill")
                skills_for_uttr.append("personal_info_skill")
                if about_news or lets_chat_about_particular_topic:
                    skills_for_uttr.append("news_api_skill")
                if enable_coronavirus or prev_active_skill == 'coronavirus_skill':
                    skills_for_uttr.append("coronavirus_skill")
                skills_for_uttr.append("factoid_qa")
            else:
                if low_priority_intent_detected:
                    skills_for_uttr.append("intent_responder")
                if enable_grounding_skill:
                    skills_for_uttr.append("grounding_skill")
                # process regular utterances
                skills_for_uttr.append("program_y")
                skills_for_uttr.append("cobotqa")
                skills_for_uttr.append("christmas_new_year_skill")
                skills_for_uttr.append("superbowl_skill")
                # skills_for_uttr.append("oscar_skill")
                skills_for_uttr.append("valentines_day_skill")
                skills_for_uttr.append("personal_info_skill")
                skills_for_uttr.append("meta_script_skill")
                if len(dialog["utterances"]) < 20:
                    # greeting skill inside itself do not turn on later than 10th turn of the conversation
                    skills_for_uttr.append("greeting_skill")
                if len(dialog["utterances"]) > 8:
                    skills_for_uttr.append("knowledge_grounding_skill")
                # hiding factoid by default, adding check for factoid classification instead
                # skills_for_uttr.append("factoid_qa")
                if (factoid_classification > factoid_prob_threshold):
                    skills_for_uttr.append("factoid_qa")
                skills_for_uttr.append("comet_dialog_skill")

                # if ner_detected:
                #     skills_for_uttr.append("reddit_ner_skill")

                if len(dialog["human_utterances"]) >= 5:
                    # can answer on 4-th user response
                    skills_for_uttr.append("convert_reddit")
                if len(dialog["utterances"]) > 14:
                    skills_for_uttr.append("alice")
                    skills_for_uttr.append("program_y_wide")
                # if len(dialog["utterances"]) > 7:
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

                linked_to_book = False
                if len(dialog["bot_utterances"]) > 0:
                    linked_to_book = any([phrase in dialog["bot_utterances"][-1]["text"]
                                          for phrase in QUESTIONS_ABOUT_BOOKS])

                if about_books or prev_active_skill == 'book_skill' or linked_to_book:
                    skills_for_uttr.append("book_skill")
                    skills_for_uttr.append("book_tfidf_retrieval")

                if about_games:
                    skills_for_uttr.append("game_cooperative_skill")

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

                if about_news or lets_chat_about_particular_topic:
                    skills_for_uttr.append("news_api_skill")

                # joke requested
                if is_joke_requested(dialog["human_utterances"][-1]):
                    # if there is no "bot" key in our dictionary, we manually create it
                    if "bot" not in dialog:
                        dialog['bot'] = {}
                    # if there is no "attributes" key in our dictionary, we manually create it
                    if "attributes" not in dialog['bot']:
                        dialog['bot']['attributes'] = {}
                    # if there is no "emotion_skill_attributes" in our dictionary, we manually create it
                    if "emotion_skill_attributes" not in dialog['bot']['attributes']:
                        dialog['bot']['attributes']['emotion_skill_attributes'] = {}

                    emotion_skill_attributes = dialog['bot']['attributes']['emotion_skill_attributes']
                    emotion_skill_attributes['state'] = "joke_requested"
                    dialog['bot']['attributes']['emotion_skill_attributes'] = emotion_skill_attributes
                    skills_for_uttr.append("joke")

                emo_prob_threshold = 0.9  # to check if any emotion has at least this prob
                for emotion, prob in emotions.items():
                    if prob == max(emotions.values()):
                        found_emotion, found_prob = emotion, prob
                cond1 = found_emotion != 'neutral' and found_prob > emo_prob_threshold
                should_run_emotion = cond1 or detect_emotion(prev_bot_uttr, dialog['human_utterances'][-1])
                good_emotion_prob = max([emotions['joy'], emotions['love']])
                bad_emotion_prob = max([emotions['anger'], emotions['fear'], emotions['sadness']])
                not_strange_emotion_prob = not (good_emotion_prob > 0.5 and bad_emotion_prob > 0.5)
                should_run_emotion = should_run_emotion and not_strange_emotion_prob
                if should_run_emotion or "how are you?" in prev_bot_uttr.get("text", "").lower():
                    skills_for_uttr.append('emotion_skill')

                for hyp in prev_user_uttr_hyp:
                    # here we just forcibly add skills which return `can_continue` and it's not `no`
                    if hyp.get("can_continue", CAN_NOT_CONTINUE) in {CAN_CONTINUE, MUST_CONTINUE}:
                        skills_for_uttr.append(hyp["skill_name"])

                if len(dialog["utterances"]) > 1:
                    # Use only misheard asr skill if asr is not confident and skip it for greeting
                    if user_uttr_annotations["asr"]["asr_confidence"] == "very_low":
                        skills_for_uttr = ["misheard_asr"]

            # always add dummy_skill
            skills_for_uttr.append("dummy_skill")
            #  no convert when about coronavirus
            if 'coronavirus_skill' in skills_for_uttr and 'convert_reddit' in skills_for_uttr:
                skills_for_uttr.remove('convert_reddit')
            if 'coronavirus_skill' in skills_for_uttr and 'comet_dialog_skill' in skills_for_uttr:
                skills_for_uttr.remove('comet_dialog_skill')

            # (yura): do we really want to always turn small_talk_skill?
            if len(dialog["utterances"]) > 14 or lets_chat_about_particular_topic:
                skills_for_uttr.append("small_talk_skill")

            if "/alexa_" in user_uttr_text:
                skills_for_uttr = ["alexa_handler"]
            logger.info(f"Selected skills: {skills_for_uttr}")
            asyncio.create_task(callback(
                task_id=payload['task_id'],
                response=list(set(skills_for_uttr))
            ))
        except Exception as e:
            logger.exception(e)
            sentry_sdk.capture_exception(e)
            asyncio.create_task(callback(
                task_id=payload['task_id'],
                response=e
            ))
