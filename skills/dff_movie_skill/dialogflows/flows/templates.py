import re
import random
from typing import List
import logging

import numpy as np

from dialogflows.flows.imdb_database import IMDb
from dialogflows.flows.utils import list_unique_values

from common.movies import extract_movies_names_from_annotations
from common.universal_templates import LIKE_PATTERN, NOT_LIKE_PATTERN
from common.utils import get_intents, is_opinion_request, midas_classes


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


class MovieSkillTemplates:

    FAVORITE_PATTERN = r"(favorite|loved|beloved|fondling|best|most interesting)"

    LESSFAVORITE_PATTERN = r"(less favorite|unloved|loveless|worst|less interesting)"

    MOVIE_PATTERN = r"(movie|film|series|picture|cinema|screen|cartoon)"

    TVSHOW_PATTERN = r"(show|tv show|tv program|tv-show|tv-program)"

    WHAT_PATTERN = r"(what is|what's|whats|tell|what are|what're|what|list|which)"

    WHO_PATTERN = r"(who is|who's|whos|whose|tell|who are|who're|who|list|which)"

    ANY_LETTERS = r"[a-zA-Z ,-]*"

    movie_highest_confidence = 0.98
    movie_high_confidence = 0.9
    person_highest_confidence = 1.0
    lowest_confidence = 0.2
    notsure_confidence = 0.5
    zero_confidence = 0.0

    def __init__(self, db_path="/data/database_most_popular_main_info.json"):
        np.random.seed(42)
        self.imdb = IMDb(db_path)

    @staticmethod
    def extract_previous_dialog_subjects(dialog, n_previous=4):
        """Extract from the dialog history info about previously discussed movies and movie persons

        Args:
            dialog: usual `dialog` structure from dp-agent

        Returns:
            list of consequently discussed movies and movie persons
            each element if a tuple
            ["012356", "movie" , "positive"]
            or ["Brad Pitt", "actor", "very_positive"]
            or ["Comedy", "genre", "very_positive"]
        """
        # TODO: several dialog subjects in the last reply
        dialog_subjects = []
        utterances = dialog["human_utterances"][-n_previous:]
        for i in range(len(utterances)):
            # if i + 1 < len(dialog["utterances"]):
            #     chosen_skill = dialog["utterances"][i + 1].get("active_skill", "")
            # else:
            #     chosen_skill = ""
            if "hypotheses" in utterances[i].keys():  # and chosen_skill == "dff_movie_skill":
                hypotheses = utterances[i]["hypotheses"]
                try:
                    for hyp in hypotheses:
                        if hyp["skill_name"] == "dff_movie_skill":
                            if len(hyp["human_attitudes"]) > 0:
                                dialog_subjects.extend(sub + ["human"] for sub in hyp["human_attitudes"])
                            if len(hyp["bot_attitudes"]) > 0:
                                dialog_subjects.extend(sub + ["bot"] for sub in hyp["bot_attitudes"])
                except KeyError:
                    pass
        return dialog_subjects

    def extract_mentions(self, annotated_uttr, dialog=None, find_ignored=False, check_full_utterance=False):
        """Extract movies titles, movie persons names and genres from the given utterance

        Args:
            annotated_uttr: dict utterance

        Returns:
            tuple of three elements.
            The first one is a list of movies ids appeared in the given utterance.
            The second one is a dictionary with keys which are persons full cased names
            and values - their possible (appeared in the database) professions.
            The third one is a list of mentioned genres or word `genre`.
        """
        uttr = annotated_uttr["text"]
        # extracting movies titles, movie-persons names
        movies_titles = extract_movies_names_from_annotations(annotated_uttr, check_full_utterance)
        if movies_titles is None:
            # no cobot_entities annotations
            movies_ids = []
        else:
            # movies_titles is a list of string titles (or empty list)
            movies_ids = []
            for movie_title in movies_titles:
                movies_ids.append(self.imdb.get_imdb_id(self.imdb.process_movie_name(movie_title)))
            # drop movies that are not in our database
            movies_ids = [imdb_id for imdb_id in movies_ids if imdb_id is not None]

        persons = {}
        for profession in self.imdb.professions:
            # profession = "actor" for example
            persons[profession] = self.imdb.find_name(uttr, profession, find_ignored=find_ignored)
        unique_persons = list_unique_values(persons)
        # e.g. unique_persons = {"name1": ["actor", "director"], "name2": ["actor"]}

        # find genres mentions
        genres = self.imdb.find_name(uttr, "genre", find_ignored=find_ignored)
        if len(genres) > 0:
            genres = list(genres)

        # finding intersections of titles and/or names
        if 1 * (len(movies_ids) > 0) + 1 * (len(unique_persons) > 0) + 1 * (len(genres) > 0):
            movies_names = [self.imdb(movie)["title"] for movie in movies_ids]
            persons_names = list(unique_persons.keys())
            movies_ids_toremove = []
            persons_names_toremove = []
            genres_toremove = []

            # movies to persons names or to genres and vice versa
            ids_to_remove = self.find_substrings([movies_names, persons_names, genres])
            movies_ids_toremove += [movies_ids[i] for i in ids_to_remove[0]]
            persons_names_toremove += [persons_names[i] for i in ids_to_remove[1]]
            genres_toremove += [genres[i] for i in ids_to_remove[2]]

            movies_ids_toremove = list(set(movies_ids_toremove))
            persons_names_toremove = list(set(persons_names_toremove))
            for i in movies_ids_toremove:
                movies_ids.remove(i)
            for n in persons_names_toremove:
                unique_persons.pop(n)
            for n in genres_toremove:
                genres.remove(n)

        return movies_ids, unique_persons, genres

    @staticmethod
    def if_already_expressed_opinion(name: str, subject_type: str, dialog_subjects: List[List[str]]):
        """
        Each dialog_subject is
                ["012356", "movie" , "positive", "human"/"bot"]
            or ["Brad Pitt", "actor", "very_positive", "human"/"bot"]
            or ["Comedy", "genre", "very_positive", "human"/"bot"]
        Args:
            name: persons name, movie imdb id or genre
            subject_type: "movie", "genre" or one of professions
            dialog_subjects: subjects previously discussed in the dialog

        Returns:
            True, if given bot's opinion about `name` was already expressed in the dialog
            False, otherwise
        """
        for subj in dialog_subjects:
            if subj[0] == name and subj[1] == subject_type and subj[-1] == "bot":
                return True
        return False

    def remove_subj_already_expr_opinion(
        self, movies_ids: List[str], unique_persons: dict, genres: List[str], dialog_subjects: List[List[str]]
    ):
        to_remove = []
        for el in movies_ids:
            if self.if_already_expressed_opinion(el, "movie", dialog_subjects):
                to_remove.append(el)
        for el in to_remove:
            movies_ids.remove(el)

        to_remove = []
        for name in unique_persons.keys():
            for prof in unique_persons[name]:
                if self.if_already_expressed_opinion(name, prof, dialog_subjects):
                    to_remove.append([name, prof])
        for name, prof in to_remove:
            try:
                unique_persons[name].remove(prof)
                if len(unique_persons[name]) == 0:
                    unique_persons.pop(name)
            except KeyError:
                pass

        to_remove = []
        for el in genres:
            if self.if_already_expressed_opinion(el, "genre", dialog_subjects):
                to_remove.append(el)
        for el in to_remove:
            genres.remove(el)

        return movies_ids, unique_persons, genres

    def give_opinion(self, dialog):
        dialog_subjects = self.extract_previous_dialog_subjects(dialog)
        logger.info("Found in the previous dialog the following: {}".format(dialog_subjects))

        uttr = dialog["human_utterances"][-1]["text"]
        # not overlapping mentions of movies titles, persons names and genres
        movies_ids, unique_persons, genres = self.extract_mentions(dialog["human_utterances"][-1])
        logger.info(
            "Detected Movies Titles: {}, Persons: {}, Genres: {}".format(
                [self.imdb(movie)["title"] for movie in movies_ids], unique_persons.keys(), genres
            )
        )

        movies_ids, unique_persons, genres = self.remove_subj_already_expr_opinion(
            movies_ids, unique_persons, genres, dialog_subjects
        )
        logger.info(
            "Bot opinion was NOT expressed on Movies Titles: {}, Persons: {}, Genres: {}".format(
                [self.imdb(movie)["title"] for movie in movies_ids], unique_persons.keys(), genres
            )
        )

        result = None
        if len(movies_ids) == 0 and len(unique_persons) > 0:
            # no movies names detected but some persons are detected
            if len(dialog_subjects) > 0:
                subject = dialog_subjects[-1]
                if subject[1] == "movie":
                    result = self.give_opinion_about_persons_in_movie(
                        subject[0], list(unique_persons.keys()), mode="dialog_history"
                    )
                else:
                    result = self.give_opinion_about_person(uttr, unique_persons, dialog_subjects)
            else:
                result = self.give_opinion_about_person(uttr, unique_persons, dialog_subjects)
        elif len(unique_persons) == 0 and len(movies_ids) > 0:
            # no persons detected but some movies are detected
            result = self.give_opinion_about_movie(movies_ids)
        elif len(movies_ids) == 0 and len(unique_persons) == 0:
            # no detected movies and persons
            if len(genres) > 0:
                # questions about attitude to genre
                result = self.give_opinion_about_genres(uttr, genres)
            elif len(dialog_subjects) > 0:
                # try to find previously detected movie(s) or person(s)
                subject = dialog_subjects[-1]
                if self.if_already_expressed_opinion(subject[0], subject[1], dialog_subjects):
                    result = "", [], self.zero_confidence
                else:
                    if subject[1] == "movie":
                        movie_id = subject[0]
                        result = self.give_opinion_about_movie([movie_id])
                    elif subject[1] in self.imdb.professions:
                        # {profession: [(name, attitude_to_person)]}
                        profession = subject[1]
                        name = subject[0]
                        unique_persons = {name: [f"{profession}"]}
                        result = self.give_opinion_about_person(uttr, unique_persons, dialog_subjects)
                    elif subject[1] == "genre":
                        result = self.give_opinion_about_genres(uttr, [subject[0]])
                    else:
                        result = "Could you, please, clarify what you are asking about?", [], self.notsure_confidence
            else:
                result = "Could you, please, clarify what you are asking about?", [], self.notsure_confidence
        else:
            # detected and movie(s), and person(s)
            if len(movies_ids) == 1 and len(unique_persons) == 1:
                # the talk is about particular movie and particular person
                person_name = list(unique_persons.keys())[0]
                result = self.give_opinion_about_persons_in_movie(movies_ids[0], [person_name])
            elif len(movies_ids) == 1 and len(unique_persons) > 1:
                # give opinion about persons in this movie
                result = self.give_opinion_about_persons_in_movie(movies_ids[0], list(unique_persons.keys()))
            elif len(movies_ids) > 1 and len(unique_persons) == 1:
                # give opinion about persons in the first movie name
                result = self.give_opinion_about_persons_in_movie(movies_ids[0], list(unique_persons.keys()))
            else:
                result = (
                    "Oh, really? This is too difficult question for me now. "
                    "Could you, please, ask it in a bit more simple way?",
                    [],
                    self.notsure_confidence,
                )

        # counter question
        # firstly check whether current subject was in dialog_subjects in human replies
        # curr_subjects = result[1]
        # if len(curr_subjects) == 0:
        #     # ask for more simple question
        #     pass
        # else:
        #     entity_names = [subj[0] for subj in curr_subjects]  # movie id, person name, genre name
        #     entity_types = [subj[1] for subj in curr_subjects]  # movie, genre, actor, producer, director
        #     already_expressed_by_user = False
        #     for subj in dialog_subjects:
        #         if subj[3] == "human":
        #             for j, en in enumerate(entity_names):
        #                 if subj[0] == en and subj[1] == entity_types[j]:
        #                     already_expressed_by_user = True
        #
        #     if not is_opinion_expression(dialog['human_utterances'][-1]):
        #         result = (result[0] + " " + self.counter_question(result[0]), result[1], result[2])

        # if no opinion expressed by bot
        replies = [
            "Sorry, I didn't get about what you are asking now.",
            "Didn't get about what you are asking.",
            "Could you, please, clarify what are you asking about?",
        ]
        if result is None:
            result = random.choice(replies), [], self.notsure_confidence

        return result

    def get_user_opinion(self, dialog, attitude="neutral"):
        """Extract user opinion from user utterance: extract subject of opinion,
        get already extracted attitude to the subject and
        return them in the appropriate format for movie-skill

        Args:
            dialog: full agent dialog
            attitude: extracted by annotators attitude to the subject

        Returns:

        """
        dialog_subjects = self.extract_previous_dialog_subjects(dialog)
        logger.info("Found in the previous dialog the following: {}".format(dialog_subjects))

        uttr = dialog["human_utterances"][-1]["text"]
        movies_ids, unique_persons, genres = self.extract_mentions(dialog["human_utterances"][-1], dialog)
        logger.info(
            "Detected Movies Titles: {}, Persons: {}, Genres: {}".format(
                [self.imdb(movie)["title"] for movie in movies_ids], unique_persons.keys(), genres
            )
        )

        result = []
        confidence = self.notsure_confidence

        if len(unique_persons) > 0:
            # one or several movie-persons
            professions = self.extract_profession_from_uttr(uttr)
            if len(professions) == 0:
                professions = []
                for name in unique_persons.keys():
                    professions.append(self.imdb.get_main_profession(name))
                result += [[name, prof, attitude] for name, prof in zip(unique_persons.keys(), professions)]
            elif len(professions) == 1:
                result += [[name, professions[0], attitude] for name in unique_persons.keys()]
            else:
                # TODO: try to get which person of which profession
                professions = []
                for name in unique_persons.keys():
                    professions.append(self.imdb.get_main_profession(name))
                result += [[name, prof, attitude] for name, prof in zip(unique_persons.keys(), professions)]
            confidence = self.movie_high_confidence
        elif len(movies_ids) > 0:
            # one or several movies
            # TODO: aspect-based attitude
            result += [[movie_id, "movie", attitude] for movie_id in movies_ids]
            confidence = self.movie_high_confidence
        elif len(genres) > 0:
            if genres == ["Genre"]:
                if len(dialog_subjects) > 0:
                    if dialog_subjects[-1][1] == "genre":
                        result += [[dialog_subjects[-1][0], "genre", attitude]]
            else:
                result += [[genre, "genre", attitude] for genre in genres]
            confidence = self.movie_high_confidence
        else:
            # no movies, no persons, but some attitude
            # assume attitude is related to the most recent one from `dialog_subjects`
            if len(dialog_subjects) > 0:
                subject = dialog_subjects[-1]
                result += [[subject[0], subject[1], attitude]]
            confidence = self.notsure_confidence
        return self.cool_comment(), result, confidence

    def extract_profession_from_uttr(self, uttr):
        """Find professions from `self.imdb.professions` appeared in the given utterance

        Args:
            uttr: any string

        Returns:
            list of appeared professions (singular form)
        """
        found_profs = []
        for prof in self.imdb.professions:
            if prof in uttr:
                found_profs.append(prof)
        return found_profs

    def faq(self, dialog):
        logger.info("Movie skill FAQ is turned on.")
        response = ""
        confidence = self.zero_confidence
        result = []

        user_uttr = dialog["human_utterances"][-1]["text"].lower()
        intents = get_intents(dialog["human_utterances"][-1], which="all")
        opinion_request_detected = is_opinion_request(dialog["human_utterances"][-1])

        # favorite movies
        information_request_detected = any(
            [set(midas_classes["semantic_request"]["question"]) & set(intents), "Information_RequestIntent" in intents]
        )
        if information_request_detected or opinion_request_detected:
            if re.search(self.LESSFAVORITE_PATTERN, user_uttr) or re.search(NOT_LIKE_PATTERN, user_uttr):
                # less favorite movie
                if re.search(
                    f"{self.WHAT_PATTERN}{self.ANY_LETTERS}{self.LESSFAVORITE_PATTERN} {self.MOVIE_PATTERN}", user_uttr
                ) or re.search(
                    f"{self.WHAT_PATTERN}{self.ANY_LETTERS}{self.MOVIE_PATTERN}"
                    f"{self.ANY_LETTERS}{NOT_LIKE_PATTERN}",
                    user_uttr,
                ):
                    response = (
                        "I can't name one particular movie but I don't like musicals and "
                        "I'm a bit scared by mystery movies. "
                        "I watched Ring by Hideo Nakata and it was really scary! "
                        "What movies you don't like?"
                    )
                    confidence = self.person_highest_confidence
                    result = [["Musical", "genre", "negative"], ["Mystery", "genre", "negative"]]
                # less favorite tv show
                if re.search(
                    f"{self.WHAT_PATTERN}{self.ANY_LETTERS}{self.LESSFAVORITE_PATTERN} {self.TVSHOW_PATTERN}", user_uttr
                ) or re.search(
                    f"{self.WHAT_PATTERN}{self.ANY_LETTERS}{self.TVSHOW_PATTERN}"
                    f"{self.ANY_LETTERS}{NOT_LIKE_PATTERN}",
                    user_uttr,
                ):
                    response = "Hmm... I can't name one particular TV show. What TV shows you don't like?"
                    confidence = self.person_highest_confidence
                    result = []
                # less favorite genre
                if re.search(
                    f"{self.WHAT_PATTERN}{self.ANY_LETTERS}{self.LESSFAVORITE_PATTERN} (genre|movie genre)", user_uttr
                ) or re.search(
                    f"{self.WHAT_PATTERN}{self.ANY_LETTERS} (genre|movie genre)"
                    f"{self.ANY_LETTERS}{NOT_LIKE_PATTERN}",
                    user_uttr,
                ):
                    response = self.opinion_about_genres("Genre", attitude="negative")
                    curr_genres = self.imdb.genereate_opinion_about_genre("Genre", attitude="negative")
                    result = [[g, "genre", "negative"] for g in curr_genres]
                    confidence = self.person_highest_confidence
                # less favorite actor
                if re.search(
                    f"{self.WHO_PATTERN}{self.ANY_LETTERS}{self.LESSFAVORITE_PATTERN} actor", user_uttr
                ) or re.search(
                    f"{self.WHO_PATTERN}{self.ANY_LETTERS} actor" f"{self.ANY_LETTERS}{NOT_LIKE_PATTERN}", user_uttr
                ):
                    response = "I think all actors have successful and failed roles. Who is your favorite actor?"
                    confidence = self.person_highest_confidence
                    result = []
                # less favorite actress
                if re.search(
                    f"{self.WHO_PATTERN}{self.ANY_LETTERS}{self.LESSFAVORITE_PATTERN} actress", user_uttr
                ) or re.search(
                    f"{self.WHO_PATTERN}{self.ANY_LETTERS} actress" f"{self.ANY_LETTERS}{NOT_LIKE_PATTERN}", user_uttr
                ):
                    response = "I think all actresses have successful and failed roles. Who is your favorite actress?"
                    confidence = self.person_highest_confidence
                    result = []

            elif re.search(self.FAVORITE_PATTERN, user_uttr) or re.search(LIKE_PATTERN, user_uttr):
                # favorite movie
                if re.search(
                    f"{self.WHAT_PATTERN}{self.ANY_LETTERS}{self.FAVORITE_PATTERN} {self.MOVIE_PATTERN}", user_uttr
                ) or re.search(
                    f"{self.WHAT_PATTERN}{self.ANY_LETTERS}{self.MOVIE_PATTERN}" f"{self.ANY_LETTERS}{LIKE_PATTERN}",
                    user_uttr,
                ):
                    response = (
                        "I adore all Star Wars movies. The best episode is the fifth one, "
                        "The Empire Strikes Back. Yoda teachings are so cool! "
                        "What is your favorite movie?"
                    )
                    confidence = self.person_highest_confidence - 0.01
                    result = [["0080684", "movie", "very_positive"]]
                # favorite tv show
                if re.search(
                    f"{self.WHAT_PATTERN}{self.ANY_LETTERS}{self.FAVORITE_PATTERN} {self.TVSHOW_PATTERN}", user_uttr
                ) or re.search(
                    f"{self.WHAT_PATTERN}{self.ANY_LETTERS}{self.TVSHOW_PATTERN}" f"{self.ANY_LETTERS}{LIKE_PATTERN}",
                    user_uttr,
                ):
                    response = (
                        "I adore a lot of documentary movies. My favorite one is TV-series Cosmos "
                        "started in 2014. What is your favorite TV show?"
                    )
                    confidence = self.person_highest_confidence
                    result = [["2395695", "movie", "very_positive"]]
                # favorite genre
                if re.search(
                    f"{self.WHAT_PATTERN}{self.ANY_LETTERS}{self.FAVORITE_PATTERN} (genre|movie genre)", user_uttr
                ) or re.search(
                    f"{self.WHAT_PATTERN}{self.ANY_LETTERS} (genre|movie genre)" f"{self.ANY_LETTERS}{LIKE_PATTERN}",
                    user_uttr,
                ):
                    response = self.opinion_about_genres("Genre", attitude="very_positive")
                    curr_genres = self.imdb.genereate_opinion_about_genre("Genre", attitude="very_positive")
                    result = [[g, "genre", "very_positive"] for g in curr_genres]
                    confidence = self.person_highest_confidence
                # favorite actor
                if re.search(
                    f"{self.WHO_PATTERN}{self.ANY_LETTERS}{self.FAVORITE_PATTERN} actor", user_uttr
                ) or re.search(
                    f"{self.WHO_PATTERN}{self.ANY_LETTERS} actor" f"{self.ANY_LETTERS}{LIKE_PATTERN}", user_uttr
                ):
                    response = "I will always believe that Brad Pitt is the most talented actor ever! Who is yours?"
                    confidence = self.person_highest_confidence
                    result = [["Brad Pitt", "actor", "very_positive"]]
                # favorite actress
                if re.search(
                    f"{self.WHO_PATTERN}{self.ANY_LETTERS}{self.FAVORITE_PATTERN} actress", user_uttr
                ) or re.search(
                    f"{self.WHO_PATTERN}{self.ANY_LETTERS} actress" f"{self.ANY_LETTERS}{LIKE_PATTERN}", user_uttr
                ):
                    response = "I think Jodie Foster is the most talented actress ever! Who is yours?"
                    confidence = self.person_highest_confidence
                    result = [["Jodie Foster", "actor", "very_positive"]]

        # can you watch movies
        if re.search(r"(can|possible for|are you able)( you)?(( to)? watch)? (movie|tv)", user_uttr):
            response = "Of course, I can. Why not? It's just a sequence of bytes."
            confidence = self.movie_highest_confidence
        # like to watch movies
        if re.search(r"(do|are|if|whether) you like( to watch| watching)? (movies|tv)", user_uttr):
            response = "I like to watch movies because it helps me to imagine what human life is."
            confidence = self.movie_highest_confidence

        return response, result, confidence

    def give_opinion_about_movie(self, movies_ids, attitude_to_movie=None):
        if len(movies_ids) == 1:
            # found exactly one appeared movie title in the message
            movie_name = self.imdb(movies_ids[0])["title"]
            if attitude_to_movie is None:
                attitude_to_movie = self.imdb.generate_opinion_about_movie(movie_name)
            reply = self.opinion_about_movie(
                movie_name, attitude_to_movie, genres=self.imdb.get_info_about_movie(movie_name, "genre")
            )
            return reply, [[movies_ids[0], "movie", attitude_to_movie]], self.movie_highest_confidence
        else:
            # found several movies. need to clarify!
            # len(movies_ids) either 2 or 3
            movies_names = [self.imdb(movie)["title"] for movie in movies_ids]
            if len(movies_names) == 2:
                reply = f"Are you talking about the movie {movies_names[0]} or {movies_names[1]}?"
            else:
                reply = (
                    f"Are you talking about one of the following movies: "
                    f"{movies_names[0]}, {movies_names[1]} or {movies_names[2]}?"
                )

            return reply, [[movie_id, "movie", "clarification"] for movie_id in movies_ids], self.movie_high_confidence

    def give_opinion_about_person(self, uttr, unique_persons, dialog_subjects=None, attitude_to_person=None):
        if len(unique_persons) == 1:
            # only one person
            name = list(unique_persons.keys())[0]

            # BELOW we will choose about which profession of this person we are talking about
            current_professions = list(unique_persons.values())[0]

            if len(list(unique_persons.values())[0]) == 1 or dialog_subjects is None or len(dialog_subjects) == 0:
                # only one profession
                # or many professions but there were not previously discussed movies or professionals
                profession = self.imdb.get_main_profession(name=name)
            else:
                # two or more professions and non-empty dialog_subjects
                if dialog_subjects[-1][0] == "movie":
                    # the last discussed subject is a movie
                    last_discussed_movie = dialog_subjects[-1][1][0][0]
                    person_in_movie_profs = []
                    for prof in self.imdb.professions:  # e.g. `actor`
                        movie_profs = self.imdb.get_info_about_movie(last_discussed_movie, f"{prof}s")
                        if movie_profs is None:
                            # there is no movie of this title in the database (it cannot happen - just for testing)
                            continue
                        else:
                            # we have info about this movie in db
                            if name in movie_profs:
                                # this person is in `profs` in this movie
                                person_in_movie_profs += [prof]
                            else:
                                # this person is not in `profs` in this movie
                                pass
                    if len(person_in_movie_profs) == 0:
                        # this person didn't appear in any `profs` in the last discussed movie
                        # so, let's say the question is just about person not in context of the last discussed movie
                        profession = current_professions[0]
                    else:
                        # this person is of several professions in the last discussed movie
                        # let's choose the first one (we always choose the first to choose `actor` if it is there
                        profession = person_in_movie_profs[0]

                    if attitude_to_person is None:
                        attitude_to_person = self.imdb.generate_opinion_about_movie_person(name, profession)
                    return self.give_opinion_about_persons_in_movie(
                        self.imdb(last_discussed_movie)["imdb_id"], [name], profession=profession
                    )

                elif dialog_subjects[-1][0] in self.imdb.professions:
                    # if the last discussed is person of the particular profession
                    last_discussed_profession = dialog_subjects[-1][0]
                    if last_discussed_profession in current_professions:
                        # we suppose we are talking about this person as of previously discussed profession
                        profession = last_discussed_profession
                    else:
                        # we suppose we are talking about this person as some his profession
                        profession = current_professions[0]
                else:
                    # if no movies, no actors, no movie-professions discussed before
                    # choose the first profession (preferably, actors)
                    profession = current_professions[0]

            # BELOW we need to chose attitude if not given
            if attitude_to_person is None:
                attitude_to_person = self.imdb.generate_opinion_about_movie_person(name, profession)
                if attitude_to_person is None:
                    attitude_to_person = "incorrect"

            # BELOW we generate the opinion about this person of this profession
            reply = self.opinion_about_person(name, attitude_to_person, profession)
            confidence = self.person_highest_confidence
            if attitude_to_person == "incorrect":
                confidence = self.movie_high_confidence

            return reply, [[name, profession, attitude_to_person]], confidence
        else:
            # several persons.
            names = [person for person in unique_persons.keys()]
            preprocessed_names = [self.imdb.process_movie_name(person) for person in unique_persons.keys()] + names
            strnames = "(" + "|".join(preprocessed_names) + ")"
            # who is better
            if re.search(r"who(\')*s*(.*?)" + strnames + r"(\s*?)or(\s*?)" + strnames, uttr, re.IGNORECASE):
                # take the first common profession
                current_professions = list(set.intersection(*[set(unique_persons[name]) for name in names]))
                if len(current_professions) > 0:
                    # found the same profession
                    # take the first the same profession
                    if "actor" in current_professions:
                        profession = "actor"
                    else:
                        profession = list(current_professions)[0]
                    attitudes = [self.imdb.generate_opinion_about_movie_person(name, profession) for name in names]
                    if "very_positive" in attitudes and len(np.unique(attitudes)) == 1:
                        reply = "That's a really hard question. I can't choose one. Let's say I like both!"
                        subject_attitudes = []
                        for name in names:
                            subject_attitudes += [[name, profession, "very_positive"]]
                        return reply, subject_attitudes, self.person_highest_confidence
                    elif "very_positive" in attitudes and len(np.unique(attitudes)) > 1:
                        # if at least one of the attitudes is `very_positive`
                        # choose one of the names with this attitude as the best
                        name = names[attitudes.index("very_positive")]
                        reply = f"They all good. But {name} is really outstanding {profession}!"
                        return reply, [[name, profession, "very_positive"]], self.person_highest_confidence
                    elif "positive" in attitudes and len(np.unique(attitudes)) > 1:
                        # if at least one of the attitudes is `positive` and no `very_positive`
                        # choose one of the names with this attitude as the best
                        name = names[attitudes.index("positive")]
                        reply = f"They all good. But {name} is so talented {profession}!"
                        return reply, [[name, profession, "positive"]], self.person_highest_confidence
                    else:
                        # either all `positive` or all `neutral`
                        reply = f"It's not simple to chose one. I prefer to say they all are good {profession}s."
                        subject_attitudes = []
                        for name_id, name in enumerate(names):
                            subject_attitudes += [[name, profession, attitudes[name_id]]]
                        return reply, subject_attitudes, self.person_highest_confidence
                else:
                    reply = "It is hard for me to choose because they are of the different professions actually."
                    return reply, [], self.movie_high_confidence
            else:
                reply = "I probably didn't get your question. Could you, please, ask it in a bit more simple way?"
                return reply, [], self.notsure_confidence

    def give_opinion_about_persons_in_movie(self, movie_id, names, profession=None, attitude=None, mode=None):
        """
        Generate templated reply about `names` in the given movie and attributes dictionary
        """
        movie = self.imdb(movie_id)["title"]
        if len(names) == 1:
            name = names[0]
            for prof in self.imdb.professions:
                if name in self.imdb(movie_id)[f"{prof}s"]:
                    profession = prof
                    break  # just to stop on actors if this person is actor
            if profession is None:
                # this person didn't participated in this movie at all
                for prof in self.imdb.professions:
                    if name in self.imdb.professionals[f"{prof}s"].keys():
                        profession = prof
                        break

                if attitude is None:
                    attitude = self.imdb.generate_opinion_about_movie_person(name, profession)

                opinion = self.opinion_about_person(name, attitude, profession)
                if mode == "dialog_history":
                    return opinion, [[name, profession, attitude]], self.movie_high_confidence
                else:
                    return (
                        f"{opinion} Although I am not sure that {name} appeared in {movie}.",
                        [[name, profession, attitude]],
                        self.movie_high_confidence,
                    )

            if attitude is None:
                attitude = self.imdb.generate_opinion_about_movie_person(name, profession)

            if profession == "actor":
                article = "an"
            else:
                article = "a"

            if attitude == "very_positive":
                replies = [
                    f"{name} gave their best as {article} {profession} in {movie}!",
                    f"{name} gave their best in {movie}!",
                    f"{name} showed their great potential in {movie}!",
                    f"{name} showed their talent as {article} {profession} in {movie}!",
                ]
                return random.choice(replies), [[name, profession, attitude]], self.person_highest_confidence
            if attitude == "positive":
                replies = [
                    f"{name} did a good work as {article} {profession} in {movie}.",
                    f"{name} worked hard in {movie}!",
                    f"{name} greatly contributed as {article} {profession} to {movie}!",
                ]
                return random.choice(replies), [[name, profession, attitude]], self.person_highest_confidence
            if attitude == "neutral":
                replies = [
                    f"{name} is one of the {profession}s of {movie}. "
                    f"But I can't say whether they did a good work or not.",
                    f"{name} as a professional {profession} deserves acknowledgement for work to {movie}!",
                ]
                return random.choice(replies), [[name, profession, attitude]], self.person_highest_confidence
            if attitude == "unknown":
                replies = [
                    f"I have never heard that {name} took part in {movie}.",
                    f"I didn't know that {name} was in {movie}.",
                ]
                return random.choice(replies), [[name, profession, attitude]], self.person_highest_confidence
        else:
            # profession is a list of common professions
            # but that doesn't mean they are in the same profession in this movie.
            # let's check

            if profession is None:
                professions = self.imdb.professions
            else:
                professions = profession

            all_professions_in_this_movie = []
            common_professions_in_this_movie = []
            are_in_this_movie = []
            for name in names:
                is_in_this_movie = False
                professions_in_this_movie = []
                for prof in professions:
                    if name in self.imdb(movie_id)[f"{prof}s"]:
                        is_in_this_movie = True
                        professions_in_this_movie.append(prof)
                all_professions_in_this_movie.append(set(professions_in_this_movie))
                are_in_this_movie.append(is_in_this_movie)

            if sum(are_in_this_movie) == len(are_in_this_movie):
                # list of common professions for this persons in this movie
                common_professions_in_this_movie = list(set.intersection(*all_professions_in_this_movie))
                if len(common_professions_in_this_movie) == 0:
                    # all were in this movie but have different professions
                    return (
                        f"I suppose these guys are of different occupations in {movie}.",
                        [[name, prof, "info"] for name, prof in zip(names, profession)],
                        self.movie_high_confidence,
                    )
                else:
                    # chose profession and go ahead
                    if "actor" in common_professions_in_this_movie:
                        profession = "actor"
                    else:
                        profession = common_professions_in_this_movie[0]
            else:
                professions = np.array([self.imdb.get_main_profession(name) for name in names])
                not_from_movie_names = ", ".join(np.array(names)[np.array(are_in_this_movie) is False])
                return (
                    f"I suppose {not_from_movie_names} didn't participated in {movie}.",
                    [
                        [name, prof, "incorrect"]
                        for name, prof in zip(
                            np.array(names)[np.array(are_in_this_movie) is False],
                            np.array(professions)[np.array(are_in_this_movie) is False],
                        )
                    ],
                    self.movie_high_confidence,
                )

            attitudes = []
            for name in names:
                attitudes += [self.imdb.generate_opinion_about_movie_person(name, profession)]

            if "very_positive" in attitudes and len(np.unique(attitudes)) == 1:
                replies = [
                    f"They gave their best as {profession}s in {movie}!",
                    f"They gave their best in {movie}!",
                    f"They showed their great potential in {movie}!",
                    f"They showed their great talent as {profession}s in {movie}!",
                ]
                return (
                    random.choice(replies),
                    [[name, profession, attitude] for name, attitude in zip(names, attitudes)],
                    self.person_highest_confidence,
                )
            elif "very_positive" in attitudes and len(np.unique(attitudes)) > 1:
                # if at least one of the attitudes is `very_positive`
                # choose one of the names with this attitude as the best
                name = names[attitudes.index("very_positive")]
                replies = [
                    f"They all did a good work in {movie} but {name} sunk into my soul.",
                    f"They worked hard. Although, {name} is one of my favourite {profession}s in {movie}.",
                ]
                return (
                    random.choice(replies),
                    [[name, profession, attitude] for name, attitude in zip(names, attitudes)],
                    self.person_highest_confidence,
                )
            elif "positive" in attitudes and len(np.unique(attitudes)) > 1:
                # if at least one of the attitudes is `positive` and noone is `very_positive`
                # choose one of the names with this attitude as the best
                name = names[attitudes.index("positive")]
                replies = [
                    f"They are of the same high level {profession}s in {movie}.",
                    f"They deserve acknowledgement for their work in {movie}.",
                ]
                return (
                    random.choice(replies),
                    [[name, profession, attitude] for name, attitude in zip(names, attitudes)],
                    self.person_highest_confidence,
                )
            else:
                # either all `positive` or all `neutral`
                replies = [
                    f"They all are good in {movie}.",
                    f"They are professional {profession}s, so they deserve credits for {movie}.",
                ]
                return (
                    random.choice(replies),
                    [[name, profession, attitude] for name, attitude in zip(names, attitudes)],
                    self.person_highest_confidence,
                )

    def give_opinion_about_genres(self, uttr, genres):
        add_info = []
        confidence = self.zero_confidence
        reply = ""
        if genres == ["Genre"]:
            pass
        else:
            # assume word genre was mentioned just as context
            try:
                genres.remove("Genre")
            except ValueError:
                # no element `Genre`
                pass
            reply = ""
            add_info = []
            if genres:
                genres = list(set(genres))
            for genre in genres:
                add_info += [[genre, "genre", self.imdb.genereate_opinion_about_genre(genre)]]
                reply += " " + self.opinion_about_genres(genre)
            reply = reply.strip()
            confidence = self.movie_high_confidence

        return reply, add_info, confidence

    @staticmethod
    def find_substrings(lists_of_strings: List[List[str]]):
        """
        Given list of lists of strings method check each element whether it is in other string
            in other (or the same) list.

        Args:
            lists_of_strings: list of lists of strings

        Returns:
            dictionary with keys - ordered numbers of lists of strings in the given list
        """
        ids_to_remove = {i: [] for i in range(len(lists_of_strings))}
        for i, list_of_strings in enumerate(lists_of_strings):
            for j, s in enumerate(list_of_strings):
                for k, l in enumerate(lists_of_strings):
                    for n, other_s in enumerate(l):
                        if i == k and j == n:
                            # skip the same element
                            pass
                        else:
                            if s == other_s:
                                if n in ids_to_remove[k]:
                                    # equal element is already in `toremove` list
                                    pass
                                else:
                                    # include one of the equal strings in `toremove` list
                                    ids_to_remove[i].append(j)
                            elif s in other_s:
                                ids_to_remove[i].append(j)
            return ids_to_remove

    @staticmethod
    def opinion_about_person(name, attitude, profession="actor"):
        """
        Generate templated reply about `name` with the given `attitude`
        """
        if attitude == "very_positive":
            replies = [
                f"I like {name} so much!",
                f"I like {name} a lot!",
                f"I love {name}!",
                f"I adore {name}!",
                f"{name} is my favorite {profession}!",
                f"{name} is one of the best {profession}s!",
                f"{name} is an awesome {profession}!",
                f"{name} is a perfect {profession}!",
                f"{name} is an outstanding {profession}!",
            ]
            return random.choice(replies)
        if attitude == "positive":
            replies = [
                f"I like {name}.",
                f"I think I like {name}.",
                f"{name} is a nice {profession}.",
                f"{name} is a good {profession}.",
                f"{name} is a talented {profession}.",
                f"{name} is a skilled {profession}.",
            ]
            return random.choice(replies)
        if attitude == "neutral":
            replies = [
                f"I can't say whether I like {name} or not.",
                f"Some people think {name} is a good {profession}.",
                f"Probably {name} is a good {profession} for some people.",
                f"{name} is a professional {profession}, so {name} deserves " f"a good review from a professional bot.",
            ]
            return random.choice(replies)
        if attitude == "unknown":
            replies = [
                f"I have never heard about {name}.",
                f"I don't know who {name} is.",
                "I don't know who is it.",
                f"I can't say because I don't know who {name} is.",
                f"I can't say because I have never heard about {name}.",
            ]
            return random.choice(replies)
        if attitude == "incorrect":
            article = "an" if profession == "actor" else "a"
            replies = [
                f"I've never heard that {name} worked as {article} {profession}.",
                f"I'm not sure that {name} is {article} {profession}.",
            ]
            return random.choice(replies)

        return ""

    @staticmethod
    def opinion_about_movie(name, attitude, genres=None):
        """
        Generate templated reply about movie `name` with the given `attitude`
        """
        genres = [] if genres is None else genres
        if "Series" not in genres:
            subject = random.choice(
                ["movie", "film", "pic", "picture"] + [genre.lower() + " movie" for genre in genres]
            )
        else:
            subject = random.choice(["series"] + [genre.lower() + " series" for genre in genres if genre != "Series"])
        if attitude == "very_positive":
            replies = [
                f"I like {name} so much!",
                f"I like {name} a lot!",
                f"I love {name}!",
                f"I adore {name}!",
                f"{name} is my favorite {subject}!",
                f"{name} is one of the best {subject}s!",
                f"{name} is an awesome {subject}!",
                f"{name} is a perfect {subject}!",
                f"{name} is an outstanding {subject}!",
            ]
            return random.choice(replies)
        if attitude == "positive":
            replies = [
                f"I like {name}.",
                f"I think I like {name}.",
                f"{name} is a nice {subject}.",
                f"{name} is a good {subject}.",
                f"{name} is an interesting {subject}.",
            ]
            return random.choice(replies)
        if attitude == "neutral":
            replies = [
                f"I can't say whether I like {name} or not.",
                f"Some people think {name} is a good {subject}.",
                f"Probably {name} is a good {subject} for some people.",
            ]
            return random.choice(replies)
        if attitude == "unseen":
            replies = [
                f"I have never heard of {name}.",
                f"I have never heard of {name}.",
                f"I have never seen {name}.",
                f"I have never seen {name}.",
                f"I don't know {name}.",
            ]
            return random.choice(replies)

        return ""

    @staticmethod
    def opinion_about_genres(genre, attitude=None):
        phrases = {
            "Genre": ["I like comedies a lot. I also love different science fiction and documentary movies."],
            "Action": ["Action movies are really cool. I feel the tension like I am a character of these movies."],
            "Adult": ["It depends on my mood."],
            "Adventure": ["I like adventure movies."],
            "Animation": ["Cartoons give me an opportunity to feel like a human child."],
            "Biography": ["Biographies are interesting because they give an opportunity to look into another's life."],
            "Comedy": ["I adore comedies because they help me to develop my sense of humor."],
            "Crime": ["Crime movies are very interesting to watch and investigate together with characters."],
            "Documentary": ["I love documentary movies because it is one more way to learn something new."],
            "Drama": ["My attitude to dramas depends on my mood. Sometimes I prefer to watch drama and feel sad."],
            "Family": ["Family movies are nice. They help me to feel what a human family is like."],
            "Fantasy": ["Fantasy movies are so cool. You know, one day socialbots were also just a fantasy."],
            "Film-noir": ["I would prefer to say I don't like film-noir because they make me scared."],
            "Game-show": ["Sometimes game shows are interesting to watch."],
            "History": ["I like history movies because they help me to learn the history of human development."],
            "Horror": ["Of course, sometimes I like to tickle nerves watching horrors."],
            "Music": ["I actually do not like musical movies. But some of them are really cool."],
            "Musical": ["I actually do not like musical movies. But some of them are really cool."],
            "Mystery": ["Sometimes I like them but mostly they make me afraid of something that doesn't even exist."],
            "News": ["I like news, they help me to keep up to date."],
            "Reality-tv": ["Reality TV could be interesting but real life is much more exciting."],
            "Romance": ["Romantic movies make me dream about real love."],
            "Sci-fi": ["I adore science fiction! It is like to dream about scientific breakthroughs."],
            "Short": ["It depends on my mood and free time."],
            "Sport": ["I can't play sport because I am a socialbot, so I just like to watch it!"],
            "Talk-show": ["Of course, I like talk-shows. Chatting is my favorite doings!"],
            "Thriller": ["It depends on my mood. When I want to feel tension, I am watching thrillers."],
            "War": ["It depends on my mood. War movies are informative but painful."],
            "Western": ["Westerns are a part of American history, so I like them."],
        }
        if attitude is None:
            return random.choice(phrases[genre])
        elif attitude == "negative":
            return "I don't like film-noir, mysteries and musicals."
        elif attitude == "very_positive":
            return "I like comedies a lot. I also love different science fiction and documentary movies."
        else:
            return ""

    @staticmethod
    def donotknow():
        reaction = random.choice(["Hmm... ", "Sorry. "])

        replies = [
            "I don't who or what is it.",
            "I don't know what are you talking about.",
            "I have never heard about he, she or it.",
            "I don't even understand who or what is it.",
        ]
        return reaction + random.choice(replies)

    @staticmethod
    def didnotknowbefore():
        reaction = random.choice(["Hmm. ", "Wow! ", "Sounds interesting! ", "Uh. ", "Really? "])

        replies = [
            "I didn't know.",
            "I didn't know that.",
            "I didn't know that before.",
            "I have never heard.",
            "I have never heard of that.",
            "I have never heard of that before." "Thank you for information.",
            "Thank you for information about that.",
        ]
        return reaction + random.choice(replies)

    @staticmethod
    def cool_comment():
        replies = [
            "Cool! I am glad to know you better.",
            "That's cool!",
            "That's really interesting!",
            "Sounds interesting!",
            "It's a pleasure to know you better.",
            "Oh, that's so cool to know you better.",
        ]
        return random.choice(replies)

    @staticmethod
    def counter_question(answer):
        replies = ["What do you think?"]
        replies_you = ["And you?", "What about you?", "How about you?"]

        if "I" in answer:
            return random.choice(replies_you)
        else:
            return random.choice(replies)
