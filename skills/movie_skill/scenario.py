import logging
import time
import re
import string
import random
from random import choice

from templates import MovieSkillTemplates
from nltk.tokenize import sent_tokenize, word_tokenize
from common.utils import get_skill_outputs_from_dialog, is_yes, is_no
from common.constants import CAN_CONTINUE
from common.universal_templates import if_switch_topic, if_lets_chat_about_topic, if_choose_topic
from common.movies import get_movie_template, offer_talk_about_movies, ABOUT_MOVIE_TITLES_PHRASES

from CoBotQA.cobotqa_service import send_cobotqa

from os import getenv
import sentry_sdk

sentry_sdk.init(getenv('SENTRY_DSN'))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

SUPER_CONFIDENCE = 1.
DEFAULT_CONFIDENCE = 0.95
NOT_SURE_CONFIDENCE = 0.5
SECOND_FACT_PROBA = 0.5


class MovieSkillScenario:
    turns_memory = 1  # it means we can continue dialog which was active in previous 2 bot answers

    def __init__(self):
        self.default_conf = 0.98
        t0 = time.time()
        self.templates = MovieSkillTemplates()
        logger.info(f"Movie Skill initialized in {time.time() - t0} sec")

        self.opinion_request = re.compile(r"(don't|do not|not|are not|are|do)?\s?you\s"
                                          r"(like|dislike|adore|hate|love|believe|consider|get|know|taste|think|"
                                          r"recognize|sure|understand|feel|fond of|care for|fansy|appeal|suppose|"
                                          r"imagine|guess)")
        self.opinion_expression = re.compile(r"(\bi\b)?\s?(don't|do not|not|am not|'m not|am|do)?\s?"
                                             r"(like|dislike|adore|hate|love|believe|consider|get|know|taste|think|"
                                             r"recognize|sure|understand|feel|fond of|care for|fansy|appeal|suppose|"
                                             r"imagine|guess)")
        self.movie_pattern = re.compile(r"(movie|film|picture|series|tv[ -]?show|reality[ -]?show|netflix|\btv\b|"
                                        r"comedy|comedies|thriller|animation|anime|talk[ -]?show|cartoon|drama|"
                                        r"fantasy)")
        self.year_template = re.compile(r"([0-9][0-9][0-9][0-9])")

        self.extra_space_template = re.compile(r"\s\s+")

    def __call__(self, dialogs):
        responses = []
        confidences = []
        human_attributes = []
        bot_attributes = []
        attributes = []

        for dialog in dialogs:
            # import json
            # logger.info(json.dumps(dialog))
            curr_user_uttr = dialog["human_utterances"][-1]
            response, confidence, human_attr, bot_attr, attr = "", 0.0, {}, {}, {}
            # not overlapping mentions of movies titles, persons names and genres
            movies_ids, unique_persons, mentioned_genres = self.templates.extract_mentions(
                curr_user_uttr["text"].lower(), find_ignored=True)
            logger.info(
                f"Current user utterance is about movies: `{curr_user_uttr['text']}`. "
                f"Detected Movies Titles: "
                f"{[self.templates.imdb(movie)['title'] for movie in movies_ids]}, "
                f"Persons: {unique_persons.keys()}, "
                f"Genres: {mentioned_genres}")

            response, _, confidence = self.templates.faq(dialog)
            if response == "":
                response, confidence, human_attr, bot_attr, attr = self.movie_scenario(
                    dialog, movies_ids, unique_persons, mentioned_genres)
                response = re.sub(self.extra_space_template, " ", response)
                if response == "" or response in ABOUT_MOVIE_TITLES_PHRASES:
                    # no answers in scenraio
                    annotations = dialog["utterances"][-1]["annotations"]
                    attitude = annotations.get("sentiment_classification", {}).get("text", [""])[0]

                    if len(dialog["bot_utterances"]) > 0:
                        prev_bot_uttr = dialog["bot_utterances"][-1]
                    else:
                        prev_bot_uttr = {"text": ""}

                    if self.is_opinion_expression(curr_user_uttr, prev_bot_uttr):
                        response, result, confidence = self.templates.get_user_opinion(dialog, attitude)
                        if len(result) > 0 and result[0][1] == "movie":
                            confidence = SUPER_CONFIDENCE
                            movie_id = result[0][0]
                            attr = {"movie_id": movie_id, "can_continue": CAN_CONTINUE,
                                    "status_line": ["opinion_request"]}
                            human_attr = {}
                            bot_attr = {}
                            for p in ["discussed_movie_titles", "discussed_movie_ids", "discussed_movie_persons",
                                      "discussed_movie_genres", "offer_talk_about_movies"]:
                                human_attr[p] = dialog["human"]["attributes"].get(p, [])

                            human_attr["discussed_movie_titles"] += [self.templates.imdb(movie_id).get("title", "")]
                            human_attr["discussed_movie_ids"] += [movie_id]

                    if self.is_opinion_request(curr_user_uttr):
                        response, result, confidence = self.templates.give_opinion(dialog)
                        if response != "":
                            if len(result) > 0 and result[0][1] == "movie":
                                confidence = SUPER_CONFIDENCE
                                movie_id = result[0][0]
                                attr = {"movie_id": movie_id, "can_continue": CAN_CONTINUE,
                                        "status_line": ["opinion_expression", "opinion_request"]}
                                human_attr = {}
                                bot_attr = {}
                                for p in ["discussed_movie_titles", "discussed_movie_ids", "discussed_movie_persons",
                                          "discussed_movie_genres", "offer_talk_about_movies"]:
                                    human_attr[p] = dialog["human"]["attributes"].get(p, [])
                                human_attr["discussed_movie_titles"] += [self.templates.imdb(movie_id).get("title", "")]
                                human_attr["discussed_movie_ids"] += [movie_id]

            responses.append(response.strip())
            confidences.append(confidence)
            human_attributes.append(human_attr)
            bot_attributes.append(bot_attr)
            attributes.append(attr)

        return responses, confidences, human_attributes, bot_attributes, attributes

    def is_about_movies(self, uttr, prev_uttr={}):
        annotations = uttr.get("annotations", {})
        is_movie_topic = "Movies_TV" in annotations.get('cobot_topics', {}).get('text', []) or \
                         "Entertainment_Movies" in annotations.get('cobot_dialogact', {}).get('topics', [])

        curr_uttr_is_about_movies = re.search(self.movie_pattern, uttr["text"].lower())
        lets_talk_about_movies = if_lets_chat_about_topic(uttr=uttr["text"].lower()) and curr_uttr_is_about_movies
        chosed_topic = if_choose_topic(prev_uttr["text"].lower()) and curr_uttr_is_about_movies

        if is_movie_topic or lets_talk_about_movies or chosed_topic or \
                ("?" in prev_uttr["text"] and curr_uttr_is_about_movies):
            return True
        else:
            return False

    def lets_chat_about_movies(self, uttr, prev_uttr={}):
        curr_uttr_is_about_movies = re.search(self.movie_pattern, uttr["text"].lower())
        lets_talk_about_movies = if_lets_chat_about_topic(uttr=uttr["text"].lower()) and curr_uttr_is_about_movies
        chosed_topic = if_choose_topic(prev_uttr["text"].lower()) and curr_uttr_is_about_movies

        if lets_talk_about_movies or chosed_topic or ("?" in prev_uttr["text"] and curr_uttr_is_about_movies):
            return True
        else:
            return False

    def is_opinion_request(self, uttr):
        annotations = uttr.get("annotations", {})
        intents = annotations.get("cobot_dialogact", {}).get("intents", [])
        intent_detected = annotations.get("intent_catcher", {}).get(
            "opinion_request", {}).get("detected") == 1 or "Opinion_RequestIntent" in intents
        if intent_detected or re.search(self.opinion_request, uttr["text"].lower()):
            return True
        else:
            return False

    def is_opinion_expression(self, uttr, prev_uttr={}):
        annotations = uttr.get("annotations", {})
        intents = annotations.get("cobot_dialogact", {}).get("intents", [])
        intent_detected = "Opinion_ExpressionIntent" in intents
        if intent_detected or re.search(self.opinion_expression, uttr["text"].lower()) or \
                re.search(self.opinion_request, prev_uttr.get("text", "").lower()):
            return True
        else:
            return False

    def is_switch_topic(self, uttr):
        annotations = uttr.get("annotations", {})
        topic_switch_detected = annotations.get("intent_catcher", {}).get("topic_switching", {}).get("detected", 0) == 1
        intents = annotations.get("cobot_dialogact", {}).get("intents", [])
        intent_detected = "Topic_SwitchIntent" in intents
        if intent_detected or topic_switch_detected or if_switch_topic(uttr["text"].lower()):
            return True
        else:
            return False

    def is_unclear_switch_topic(self, uttr):
        annotations = uttr.get("annotations", {})
        topic_switch_detected = annotations.get("intent_catcher", {}).get("topic_switching", {}).get("detected", 0) == 1
        intents = annotations.get("cobot_dialogact", {}).get("intents", [])
        intent_detected = "Topic_SwitchIntent" in intents
        if intent_detected or topic_switch_detected or if_lets_chat_about_topic(uttr["text"].lower()) or \
                if_switch_topic(uttr["text"].lower()):
            return True
        else:
            return False

    def movie_scenario(self, dialog, movies_ids=[], unique_persons={}, mentioned_genres=[]):
        human_attr = {}
        bot_attr = {}
        for p in ["discussed_movie_titles", "discussed_movie_ids", "discussed_movie_persons",
                  "discussed_movie_genres", "offer_talk_about_movies"]:
            human_attr[p] = dialog["human"]["attributes"].get(p, [])

        curr_user_uttr = dialog["human_utterances"][-1]
        prev_movie_skill_outputs = get_skill_outputs_from_dialog(
            dialog["utterances"][-self.turns_memory * 2 - 1:], "movie_skill", activated=True)
        if len(dialog["bot_utterances"]) > 0:
            prev_bot_uttr = dialog["bot_utterances"][-1]
        else:
            prev_bot_uttr = {"text": ""}

        if len(prev_movie_skill_outputs) > 0:
            # movie skill was active in last `self.turns_memory` turns
            prev_status_line = prev_movie_skill_outputs[-1].get("status_line", [""])
            prev_status = prev_status_line[-1]
            if (prev_status not in ["finished", "clarification"] and self.is_unclear_switch_topic(curr_user_uttr)) or \
                    (prev_status in ["finished", "clarification"] and self.is_switch_topic(curr_user_uttr)):
                # user wants to switch the topic while we are in the script
                response, confidence = "What do you want to talk about?", NOT_SURE_CONFIDENCE
                attr = {"status_line": prev_status_line + ["finished"], "can_continue": CAN_CONTINUE}
            elif prev_status == "finished" or prev_status == "":
                if len(movies_ids) > 0:
                    curr_movie_id = movies_ids[-1]
                    if curr_movie_id not in human_attr["discussed_movie_ids"]:
                        # previous script was finished, currently we have a new movie id to discuss
                        response, confidence, human_attr, bot_attr, attr = self.first_reply_when_about_movies(
                            curr_user_uttr, curr_movie_id, human_attr, bot_attr)
                    else:
                        # current movie was already discussed
                        offer = offer_talk_about_movies(human_attr)
                        response = f"We have talked about this movie previously. " \
                                   f"{get_movie_template('lets_talk_about_other_movie')} {offer}"
                        confidence = DEFAULT_CONFIDENCE
                        attr = {"status_line": ["finished"], "can_continue": CAN_CONTINUE}
                        human_attr["offer_talk_about_movies"] += [offer]
                elif is_no(curr_user_uttr) or if_switch_topic(curr_user_uttr["text"].lower()):
                    response = "What do you want to talk about?"
                    confidence = NOT_SURE_CONFIDENCE
                    attr = {"status_line": prev_status_line + ["finished"], "can_continue": CAN_CONTINUE}
                elif len(prev_movie_skill_outputs) > 2 and \
                        prev_movie_skill_outputs[-3].get("status_line", [""]) == ["finished"] and \
                        prev_movie_skill_outputs[-2].get("status_line", [""]) == ["finished"]:
                    response = f"{get_movie_template('dont_know_movie_title_at_all')} " \
                               f"{get_movie_template('lets_talk_about_other_movie')}"
                    confidence = DEFAULT_CONFIDENCE
                    attr = {"status_line": ["finished"], "can_continue": CAN_CONTINUE}
                elif len(prev_movie_skill_outputs) > 1 and \
                        prev_movie_skill_outputs[-2].get("status_line", [""]) == ["finished"]:
                    response = f"{get_movie_template('dont_know_movie_title_at_all')} " \
                               f"{get_movie_template('lets_talk_about_other_movie')}"
                    confidence = DEFAULT_CONFIDENCE
                    attr = {"status_line": ["finished"], "can_continue": CAN_CONTINUE}
                else:
                    offer = offer_talk_about_movies(human_attr)
                    response = f"{offer}"
                    confidence = DEFAULT_CONFIDENCE
                    attr = {"status_line": ["finished"], "can_continue": CAN_CONTINUE}
                    human_attr["offer_talk_about_movies"] += [offer]
            else:
                # some movie scenario started and not finished
                response, confidence, human_attr, bot_attr, attr = self.get_next_response_movie_scenario(
                    curr_user_uttr, prev_bot_uttr, prev_movie_skill_outputs,
                    movies_ids, unique_persons, mentioned_genres, human_attr, bot_attr)
        # elif len(movies_ids) > 0 and self.is_about_movies(curr_user_uttr, prev_bot_uttr):
        #     response, confidence, human_attr, bot_attr, attr = self.first_reply_when_about_movies(
        #         curr_user_uttr, movies_ids[-1], human_attr, bot_attr)
        elif self.lets_chat_about_movies(curr_user_uttr, prev_bot_uttr):
            # user wants to talk about movies. offer quesiton about movies
            offer = offer_talk_about_movies(human_attr)
            response = offer
            confidence = SUPER_CONFIDENCE
            attr = {"status_line": ["finished"], "can_continue": CAN_CONTINUE}
            human_attr["offer_talk_about_movies"] += [offer]
        else:
            response, confidence, human_attr, bot_attr, attr = "", 0.0, {}, {}, {}

        return response, confidence, human_attr, bot_attr, attr

    def clarify_movie_title(self, curr_user_uttr, movie_id):
        movie_title = self.templates.imdb(movie_id)["title"]
        movie_type = self.templates.imdb.get_movie_type(movie_id)
        logger.info(f"Clarify movie title `{movie_title}` from user utterance "
                    f"`{curr_user_uttr['text']}`.")
        response = f"{get_movie_template('clarification_template', movie_type=movie_type)} " \
                   f"{movie_type} '{movie_title}'?"
        confidence = 1.
        attr = {"movie_id": movie_id, "status_line": ["clarification"], "can_continue": CAN_CONTINUE}
        return response, confidence, attr

    def remove_punct_and_articles(self, s, lowecase=True):
        articles = ['a', "an", 'the']
        if lowecase:
            s = s.lower()
        no_punct = ''.join([c for c in s if c not in string.punctuation])
        no_articles = ' '.join([w for w in word_tokenize(no_punct) if w.lower() not in articles])
        return no_articles

    def first_reply_when_about_movies(self, curr_user_uttr, movie_id, human_attr, bot_attr):
        # let's talk about movie
        movie_title = self.templates.imdb(movie_id)["title"]
        logger.info(f"First reply on extracted movie `{movie_title}` from user utterance "
                    f"`{curr_user_uttr['text']}`.")
        if self.remove_punct_and_articles(curr_user_uttr["text"]) == self.remove_punct_and_articles(movie_title):
            # full user utterance is a movie title -> consider full match
            logger.info("Full match of user uttr and movie title.")
            response, confidence, human_attr, bot_attr, attr = self.opinion_expression_and_request(
                movie_id, [], human_attr, bot_attr)
        else:
            logger.info("Not full match of user uttr and movie title. Clarify title.")
            response, confidence, attr = self.clarify_movie_title(curr_user_uttr, movie_id)

        return response, confidence, human_attr, bot_attr, attr

    def opinion_expression_and_request(self, movie_id, prev_status_line, human_attr, bot_attr):
        movie_title = self.templates.imdb(movie_id).get("title", "")
        movie_type = self.templates.imdb.get_movie_type(movie_id)
        logger.info(f"Opinion expression and opinion request for {movie_type} title `{movie_title}`.")

        reply, _, confidence = self.templates.give_opinion_about_movie([movie_id])
        if confidence >= 0.9 and len(reply) > 0 and len(movie_title) > 0:
            response = f"{get_movie_template('heard_about_template', movie_type=movie_type)} {reply} " \
                       f"{get_movie_template('opinion_request_about_movie', movie_type=movie_type)}"
            confidence = SUPER_CONFIDENCE
            attr = {"movie_id": movie_id, "can_continue": CAN_CONTINUE,
                    "status_line": prev_status_line + ["confirmation", "opinion_expression", "opinion_request"]}
            human_attr["discussed_movie_titles"] += [self.templates.imdb(movie_id).get("title", "")]
            human_attr["discussed_movie_ids"] += [movie_id]
        else:
            offer = offer_talk_about_movies(human_attr)
            response = f"{get_movie_template('dont_know_movie_title_at_all', movie_type=movie_type)} " \
                       f"{get_movie_template('lets_talk_about_other_movie', movie_type=movie_type)} {offer}"
            confidence = DEFAULT_CONFIDENCE
            attr = {"status_line": prev_status_line + ["finished"], "can_continue": CAN_CONTINUE}
            human_attr["offer_talk_about_movies"] += [offer]
        return response, confidence, human_attr, bot_attr, attr

    def after_clarification(self, curr_user_uttr, prev_movie_skill_outputs,
                            movies_ids, human_attr, bot_attr, prev_status_line, movie_id):
        if is_yes(curr_user_uttr):
            logger.info(f"User confirmed movie title after clarification. Start script.")
            response, confidence, human_attr, bot_attr, attr = self.opinion_expression_and_request(
                movie_id, prev_status_line, human_attr, bot_attr)
        elif len(movies_ids) > 0 and len(prev_movie_skill_outputs) >= 2 and \
                prev_movie_skill_outputs[-2].get("states", "") != "clarification":
            movies_ids = [mid for mid in movies_ids if mid != movie_id]
            if len(movies_ids) == 0:
                logger.info(f"Extracted the same movie title after clarification. Offer talk about movies.")
                offer = offer_talk_about_movies(human_attr)
                response = f"{get_movie_template('dont_know_movie_title_at_all')} " \
                           f"{get_movie_template('lets_talk_about_other_movie')} {offer}"
                confidence = DEFAULT_CONFIDENCE
                attr = {"status_line": prev_status_line + ["finished"], "can_continue": CAN_CONTINUE}
                human_attr["offer_talk_about_movies"] += [offer]
            else:
                logger.info(f"Extracted another movie title after clarification. Clarify for the second time.")
                curr_movie_id = movies_ids[-1]
                response, confidence, attr = self.clarify_movie_title(curr_user_uttr, curr_movie_id)
                attr["can_continue"] = CAN_CONTINUE
        elif len(prev_status_line) >= 2 and prev_status_line[-2] == "clarification":
            logger.info(f"Didn't extracted another movie title after clarification. Offer talk about movies.")
            offer = offer_talk_about_movies(human_attr)
            response = f"{get_movie_template('dont_know_movie_title_at_all')} " \
                       f"{get_movie_template('lets_talk_about_other_movie')} {offer}"
            confidence = DEFAULT_CONFIDENCE
            attr = {"status_line": prev_status_line + ["finished"], "can_continue": CAN_CONTINUE}
            human_attr["offer_talk_about_movies"] += [offer]
        else:
            logger.info(f"Didn't extracted movie title after the first clarification. Offer talk about movies.")
            offer = offer_talk_about_movies(human_attr)
            response = f"{get_movie_template('dont_know_movie_title_at_all')} " \
                       f"{get_movie_template('lets_talk_about_other_movie')} {offer}"
            confidence = DEFAULT_CONFIDENCE
            attr = {"status_line": prev_status_line + ["finished"], "can_continue": CAN_CONTINUE}
            human_attr["offer_talk_about_movies"] += [offer]
        return response, confidence, human_attr, bot_attr, attr

    def ask_do_you_know_question(self, movie_id, movie_title, movie_type, prev_status_line, human_attr, bot_attr):
        question_type = choice(["cast", "year", "genre"])
        logger.info(f"Asking question about `{movie_title}` of type `{question_type}`.")
        if question_type == "cast":
            response = f"Do you know who are the leading actors of the {movie_type} {movie_title}?"
        elif question_type == "year":
            response = f"Do you know the year of release of the {movie_type} {movie_title}?"
        else:
            response = f"Do you know the genre of the {movie_type} {movie_title}?"
        confidence = SUPER_CONFIDENCE
        attr = {"movie_id": movie_id, "can_continue": CAN_CONTINUE,
                "status_line": prev_status_line + ["do_you_know_question"]}
        return response, confidence, human_attr, bot_attr, attr

    def check_answer_to_do_you_know_question(
            self, curr_user_uttr, movie_id, movie_title, movie_type, prev_status_line,
            prev_movie_skill_outputs, unique_persons, mentioned_genres, human_attr, bot_attr):
        question_text = prev_movie_skill_outputs[-1].get("text", "")
        logger.info(f"Check user's answer to do-you-know question about `{movie_title}`: `{question_text}`.")
        confidence = SUPER_CONFIDENCE
        attr = {"movie_id": movie_id, "can_continue": CAN_CONTINUE,
                "status_line": prev_status_line + ["comment_to_question"]}
        if "who are the leading actors" in question_text:
            result = self.templates.imdb.get_info_about_movie(movie_title, "actors")
            if result is not None:
                result = f"The leading actors are {', '.join(result)}."
            else:
                result = send_cobotqa(f"who stars in {movie_type} {movie_title}?")
            if len(unique_persons) > 0 and all([name in result for name in list(unique_persons.keys())]):
                if len(unique_persons) > 1:
                    response = "Great! All those people are from main cast."
                else:
                    response = "Great! This person is from main cast."
            elif is_no(curr_user_uttr):
                response = f"{result}"
            else:
                response = f"Oops! No. {result}"
        elif "the year of release of" in question_text:
            result = self.templates.imdb.get_info_about_movie(movie_title, "year")
            if result is not None:
                year = int(result)
                result = f"The release year is {int(result)}."
            else:
                result = send_cobotqa(f"release year of {movie_type} {movie_title}?")
                year = re.search(self.year_template, result)
                if year:
                    year = year[0]
                else:
                    year = "Haha! I actually also do not know it."

            if str(year) in curr_user_uttr["text"].lower():
                response = "Exactly! You correctly named the release year."
            elif is_no(curr_user_uttr):
                response = f"{result}"
            else:
                response = f"Oops! No. {result}"
        elif "the genre of the" in question_text:
            result = self.templates.imdb.get_info_about_movie(movie_title, "genre")
            if result is not None:
                if len(result) == 1:
                    result = f"The genre of the {movie_type} is {', '.join(result)}."
                else:
                    result = f"The genres of the {movie_type} are {', '.join(result)}."
            else:
                result = send_cobotqa(f"genre of {movie_type} {movie_title}?")
            if len(mentioned_genres) > 0 and any([name in result for name in mentioned_genres]):
                response = f"Great! {result}"
            elif is_no(curr_user_uttr):
                response = f"{result}"
            else:
                response = f"Oops! No. {result}"
        else:
            response, confidence, attr = "", 0.0, {}
        return response, confidence, human_attr, bot_attr, attr

    def generate_fact_from_cobotqa(self, request_about, movie_id, movie_title, movie_type, prev_status_line,
                                   human_attr, bot_attr):
        fact = send_cobotqa(f"{request_about} {movie_type} {movie_title}?")
        logger.info(f"Generated fact about `{movie_title}`: {fact}.")
        if len(fact) > 0:
            sentences = sent_tokenize(fact.replace(".,", "."))
            if len(sentences[0]) < 100 and "fact about" in sentences[0]:
                fact = " ".join(sentences[1:3])

            response = "Did you know that " + fact
            confidence = SUPER_CONFIDENCE
            attr = {"movie_id": movie_id, "can_continue": CAN_CONTINUE,
                    "status_line": prev_status_line + ["fact"]}
        else:
            response, confidence, attr = "", 0.0, {}

        return response, confidence, human_attr, bot_attr, attr

    def lets_talk_about_movie_offer(self, prev_status_line, human_attr, bot_attr):
        # facts are done. offer to talk about other movie.
        offer = offer_talk_about_movies(human_attr)
        logger.info(f"Offer quesiton about movie `{offer}`.")
        response = f"{offer}"
        confidence = DEFAULT_CONFIDENCE
        attr = {"status_line": prev_status_line + ["finished"], "can_continue": CAN_CONTINUE}
        human_attr["offer_talk_about_movies"] += [offer]

        return response, confidence, human_attr, bot_attr, attr

    def get_next_response_movie_scenario(self, curr_user_uttr, prev_bot_uttr, prev_movie_skill_outputs,
                                         movies_ids, unique_persons, mentioned_genres, human_attr, bot_attr):
        # ["confirmation", "opinion_expression", "opinion_request", "user_opinion_comment",
        #  "do_you_know_question", "comment_to_question", "fact", "finished"]
        prev_status_line = prev_movie_skill_outputs[-1].get("status_line", [""])
        prev_status = prev_status_line[-1]
        movie_id = prev_movie_skill_outputs[-1].get("movie_id", "")
        movie_title = self.templates.imdb(movie_id)["title"]
        movie_type = self.templates.imdb.get_movie_type(movie_id)

        if prev_status == "clarification":  # -> opinion_request
            response, confidence, human_attr, bot_attr, attr = self.after_clarification(
                curr_user_uttr, prev_movie_skill_outputs, movies_ids, human_attr, bot_attr, prev_status_line, movie_id)
        elif prev_status == "confirmation":  # -> opinion_request
            # for now can not happen
            response, confidence, human_attr, bot_attr, attr = self.opinion_expression_and_request(
                movie_id, prev_status_line, human_attr, bot_attr)
        elif prev_status == "opinion_expression":  # -> opinion_request
            # for now can not happen
            if "opinion_request" not in prev_status_line:
                confidence = SUPER_CONFIDENCE
                response = get_movie_template('opinion_request_about_movie', movie_type=movie_type)
                attr = {"movie_id": movie_id, "status_line": prev_status_line + ["opinion_request"],
                        "can_continue": CAN_CONTINUE}
            else:
                response, confidence, human_attr, bot_attr, attr = self.ask_do_you_know_question(
                    movie_id, movie_title, movie_type, prev_status_line, human_attr, bot_attr)
        elif prev_status == "opinion_request":  # -> user_opinion_comment
            sentiment = curr_user_uttr["annotations"].get("sentiment_classification",
                                                          {'text': ['neutral', 1.]})["text"][0]
            response, confidence, human_attr, bot_attr, attr = self.ask_do_you_know_question(
                movie_id, movie_title, movie_type, prev_status_line, human_attr, bot_attr)
            response = f"{get_movie_template('user_opinion_comment', subcategory=sentiment, movie_type=movie_type)} " \
                       f"{response}"
            attr["status_line"] = prev_status_line + ["user_opinion_comment", "do_you_know_question"]
        elif prev_status == "user_opinion_comment":  # -> do_you_know_question
            response, confidence, human_attr, bot_attr, attr = self.ask_do_you_know_question(
                movie_id, movie_title, movie_type, prev_status_line, human_attr, bot_attr)
        elif prev_status == "do_you_know_question":  # -> comment_to_question
            response, confidence, human_attr, bot_attr, attr = self.check_answer_to_do_you_know_question(
                curr_user_uttr, movie_id, movie_title, movie_type, prev_status_line,
                prev_movie_skill_outputs, unique_persons, mentioned_genres, human_attr, bot_attr)
        elif prev_status == "comment_to_question":  # -> fact
            logger.info("Generate one more fact.")
            response, confidence, human_attr, bot_attr, attr = self.generate_fact_from_cobotqa(
                "awards of", movie_id, movie_title, movie_type, prev_status_line, human_attr, bot_attr)
            if response == "":
                response, confidence, human_attr, bot_attr, attr = self.generate_fact_from_cobotqa(
                    "tagline of", movie_id, movie_title, movie_type, prev_status_line, human_attr, bot_attr)
                if response == "":
                    response, confidence, human_attr, bot_attr, attr = self.generate_fact_from_cobotqa(
                        "fact about", movie_id, movie_title, movie_type, prev_status_line, human_attr, bot_attr)
        elif prev_status == "fact" and random.random() < SECOND_FACT_PROBA:  # -> fact
            logger.info("Decided to generate one more fact.")
            response, confidence, human_attr, bot_attr, attr = self.generate_fact_from_cobotqa(
                "fact about", movie_id, movie_title, movie_type, prev_status_line, human_attr, bot_attr)
            if response.lower() == prev_bot_uttr["text"].lower():
                response, confidence, human_attr, bot_attr, attr = self.lets_talk_about_movie_offer(
                    prev_status_line, human_attr, bot_attr)
                response = f"{get_movie_template('lets_talk_about_other_movie')} " + response
        else:  # -> finished + offer talk about movies
            logger.info("Finish chat about considered movie. Offer new one.")
            response, confidence, human_attr, bot_attr, attr = self.lets_talk_about_movie_offer(
                prev_status_line, human_attr, bot_attr)
            comment = choice(["That's okay.", "Let's move on.", "Let's change the subject."])
            response = f"{comment} {get_movie_template('lets_talk_about_other_movie')} " + response

        return response, confidence, human_attr, bot_attr, attr

    @staticmethod
    def get_titles_in_quotes(text):
        return re.findall(r'"([a-zA-Z0-9\s:\.!\?,-]+)"', text)
