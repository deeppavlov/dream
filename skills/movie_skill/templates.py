import re
import logging

import numpy as np

from imdb_database import IMDb
from utils import list_unique_values


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


class MovieSkillTemplates:
    def __init__(self, db_path="./databases/imdb_dataset_58k.json"):
        np.random.seed(42)
        self.imdb = IMDb(db_path)

    def give_opinion(self, dialog):
        # TODO add all previos attitude to attributes
        # TODO: add check whether the attitude is already in persona or attributes
        # generate_opinion should give something from `very_positive`, `positive`, `neutral`, `unseen`
        # answer to OpinionRequestIntent
        # TODO answers to questions like `Do you like movies of this genre/type? `
        uttr = dialog["utterances"][-1]["text"]
        # nouns = dialog["utterances"][-1]["annotations"]["cobot_nounphrases"]

        # let's collect about which movies and persons we were talking about
        dialog_subjects = []
        # list, each element is a tuple
        # e.g. ("movie", [("The Avengers", "positive"), ]) or ("actor", [("Brad Pitt", "very_positive")])

        for i in range(len(dialog["utterances"])):
            if i + 1 < len(dialog["utterances"]):
                chosen_skill = dialog["utterances"][i + 1].get("active_skill", "")
            else:
                chosen_skill = ""
            if "hypotheses" in dialog["utterances"][i].keys() and chosen_skill == "movie_skill":
                hypotheses = dialog["utterances"][i]["hypotheses"]
                try:
                    movie_skill_output = {}
                    for hyp in hypotheses:
                        if hyp["skill_name"] == "movie_skill":
                            movie_skill_output = hyp
                    dialog_subjects.append(
                        ("movie", [movie for movie in movie_skill_output["movie"] if movie[1] != "clarification"]))
                except KeyError:
                    pass
                    # dialog_subjects.append(
                    #     ("movie", []))
                for prof in self.imdb.professions:
                    try:
                        movie_skill_output = {}
                        for hyp in hypotheses:
                            if hyp["skill_name"] == "movie_skill":
                                movie_skill_output = hyp
                        dialog_subjects.append(
                            (prof, [person for person in movie_skill_output[prof] if person[1] != "clarification"]))
                    except KeyError:
                        pass
                        # dialog_subjects.append(
                        #     (prof, []))

        logger.info("Found in the dialog the following: {}".format(dialog_subjects))
        # find appeared movies names in reply
        movies_ids = self.imdb.find_name(uttr, "movie")
        if len(movies_ids) > 0:
            movies_ids = list(movies_ids)
            logger.info("Detected movies: `{}` in `{}`".format([self.imdb(movie)["title"] for movie in movies_ids],
                                                               uttr))
        # find appeared persons names in reply of particular professions (actors, directors)
        persons = {}
        for profession in self.imdb.professions:
            # profession = "actor" for example
            persons[profession] = self.imdb.find_name(uttr, profession)
        unique_persons = list_unique_values(persons)
        # for name in unique_persons.keys():
        #     unique_persons[name] = [profs[:-1] for profs in unique_persons[name]]
        # e.g. unique_persons = {"name1": ["actor", "director"], "name2": ["actor"]}

        if unique_persons:
            logger.info("Unique persons: {}".format(unique_persons))

        if len(movies_ids) > 0 and len(unique_persons) > 0:
            movies_names = [self.imdb(movie)["title"] for movie in movies_ids]
            persons_names = list(unique_persons.keys())
            movies_ids_toremove = []
            persons_names_toremove = []
            for i, movie_name in enumerate(movies_names):
                for person_name in persons_names:
                    if movie_name in person_name:
                        movies_ids_toremove.append(movies_ids[i])
                    elif person_name in movie_name:
                        persons_names_toremove.append(person_name)

            movies_ids_toremove = list(set(movies_ids_toremove))
            persons_names_toremove = list(set(persons_names_toremove))
            for i in movies_ids_toremove:
                movies_ids.remove(i)
            for n in persons_names_toremove:
                unique_persons.pop(n)

            logger.info("Fixed. Final detected movies: {}, Persons: {}".format(
                [self.imdb(movie)["title"] for movie in movies_ids], unique_persons.keys()))

        if len(movies_ids) == 0 and len(unique_persons) > 0:
            # no movies names detected but some persons are detected
            return self.give_opinion_about_person(uttr, unique_persons, dialog_subjects)
        elif len(unique_persons) == 0 and len(movies_ids) > 0:
            # no persons detected but some movies are detected
            return self.give_opinion_about_movie(movies_ids)
        elif len(movies_ids) == 0 and len(unique_persons) == 0:
            # TODO: questions about favourite movies, genres, actors, directors, movie topics, movie epochs etc.
            # no detected movies and persons
            if len(dialog_subjects) > 0:
                # try to find previously detected movie(s) or person(s)
                subject = dialog_subjects[-1]
                if subject[0] == "movie":
                    if len(subject[1]) == 1:
                        movie_name = subject[1][0][0]
                        attitude = subject[1][0][1]
                        return self.give_opinion_about_movie(movie_name, attitude)
                    else:
                        movies = [m[0] for m in subject[1]]
                        return self.give_opinion_about_movie(movies)
                elif subject[0] in self.imdb.professions:
                    # {profession: [(name, attitude_to_person)]}
                    profession = subject[0]
                    names = [p[0] for p in subject[1]]
                    attitudes = [p[1] for p in subject[1]]
                    unique_persons = {name: [f"{profession}"] for name in names}
                    # attitudes will be used only if only one person appeared
                    return self.give_opinion_about_person(uttr, unique_persons, dialog_subjects, attitudes[0])
        else:
            # detected and movie(s), and person(s)
            if len(movies_ids) == 1 and len(unique_persons) == 1:
                # the talk is about particular movie and particular person
                person_name = list(unique_persons.keys())[0]
                return self.give_opinion_about_persons_in_movie(
                    movies_ids[0], [person_name])
            elif len(movies_ids) == 1 and len(unique_persons) > 1:
                # give opinion about persons in this movie
                return self.give_opinion_about_persons_in_movie(
                    movies_ids[0], list(unique_persons.keys()))
            elif len(movies_ids) > 1 and len(unique_persons) == 1:
                # give opinion about persons in the first movie name
                return self.give_opinion_about_persons_in_movie(
                    movies_ids[0], list(unique_persons.keys()))
            else:
                return "Oh, really? This is too difficult question for me now. " \
                       "Could you, please, ask it in a bit more simple way?", {}

        replies = ["Sorry, I didn't get about what you are asking now.",
                   "Didn't get about what you are asking.",
                   "Could you, please, clarify what are you asking about?"
                   ]
        return np.random.choice(replies), {}

    def give_factual_answer(self, dialog):
        # answer to InfoRequestIntent
        # qa answers?
        # TODO: remove "do you know", "tell me"
        # uttr = dialog["utterances"][-1]["text"]
        # nouns = dialog["utterances"][-1]["annotations"]["cobot_nounphrases"]
        # # remove some `please`, "could you" and like this from user's question
        # uttr = re.sub(r"(\s|,\s)?please,?", "", uttr.lower())
        # uttr = re.sub(r"(can|could|would)\s(you)?\s?", "", uttr)
        # # replace `do you know what` to `what`
        # # replace `search for the genre of this movie` to `what the genre of this movie`
        # uttr = re.sub(r"((tell\sme|say|guess)(\swhat)?|do\syou\sknow(\swhat)?|look\sfor|find|google|search\sfor)",
        #               "what", uttr)

        # return self.donotknow()
        return ""

    def ask_factual_question(self, dialog):
        pass

    def request_opinion(self, dialog):
        pass

    def request_personal_info(self, dialog):
        pass

    def give_comment(self, dialog):
        pass

    def recommend(self, dialog):
        pass

    def give_opinion_about_movie(self, movies_ids, attitude_to_movie=None):
        if len(movies_ids) == 1:
            # found exactly one appeared movie title in the message
            movie_name = self.imdb(movies_ids[0])["title"]
            if attitude_to_movie is None:
                attitude_to_movie = self.imdb.generate_opinion_about_movie(movie_name)
            reply = self.opinion_about_movie(movie_name, attitude_to_movie,
                                             genres=self.imdb.get_info_about_movie(movie_name, "genre"))
            return reply, {"movie": [(movie_name, attitude_to_movie)]}
        else:
            # found several movies. need to clarify!
            # len(movies_ids) either 2 or 3
            movies_names = [self.imdb(movie)["title"] for movie in movies_ids]
            if len(movies_names) == 2:
                reply = f"Are you talking about the movie {movies_names[0]} or {movies_names[1]}?"
            else:
                reply = f"Are you talking about one of the following movies: " \
                        f"{movies_names[0]}, {movies_names[1]} or {movies_names[2]}?"

            return reply, {"movie": [(movies_names, "clarification")]}

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
                    # dialog_subject = [("movie", [("John Smith", "positive")])]
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
                        self.imdb(last_discussed_movie)["imdb_id"], [name], profession=profession)

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

            return reply, {profession: [(name, attitude_to_person)]}
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
                    attitudes = [self.imdb.generate_opinion_about_movie_person(name, profession)
                                 for name in names]
                    if "very_positive" in attitudes and len(np.unique(attitudes)) == 1:
                        reply = f"That's a really hard question. I can't choose one. Let's say I like both!"
                        subject_attitudes = {profession: []}
                        for name in names:
                            subject_attitudes[profession] += [(name, "very_positive")]
                        return reply, subject_attitudes
                    elif "very_positive" in attitudes and len(np.unique(attitudes)) > 1:
                        # if at least one of the attitudes is `very_positive`
                        # choose one of the names with this attitude as the best
                        name = names[attitudes.index("very_positive")]
                        reply = f"They all good. But {name} is really outstanding {profession}!"
                        return reply, {profession: [(name, "very_positive")]}
                    elif "positive" in attitudes and len(np.unique(attitudes)) > 1:
                        # if at least one of the attitudes is `positive` and no `very_positive`
                        # choose one of the names with this attitude as the best
                        name = names[attitudes.index("positive")]
                        reply = f"They all good. But {name} is so talented {profession}!"
                        return reply, {profession: [(name, "positive")]}
                    else:
                        # either all `positive` or all `neutral`
                        reply = f"It's not simple to chose one. I prefer to say they all are good {profession}s."
                        subject_attitudes = {profession: []}
                        for name_id, name in enumerate(names):
                            subject_attitudes[profession] += [(name, attitudes[name_id])]
                        return reply, subject_attitudes
                else:
                    reply = "It is hard for me to choose because they are of the different professions actually."
                    return reply, {}
            else:
                reply = "I probably didn't get your question. Could you, please, ask it in a bit more simple way?"
                return reply, {}

    def faq_about_genres(self, question):
        # what_genre = [r"(what|which)(\')*s*(.*?)(is|are|was|were|will be)*?(.*?)(the|a|its)*?(\s*?)genres?",
        #               # what/which is/are the/a genre(s) of this movie/moviename?
        #               r"^genres?\??$",  # Genre?
        #               ]
        # varity_genre = [
        #     r"(is|are|was|were|will be)+?\s(that|this|these)(.*?)" + all_genres_str + "(.*?)or(.*?)" + all_genres_str,
        #     # is that movie of comedy or thriller?
        #     ]
        # proposed_genre = [r"(is|are|was|were|will be)+?\s(that|this|these|it|they)(.*?)" + all_genres_str,
        #                   # is that movie of comedy genre?
        #                   ]
        # movie_genres = self.imdb.get_info_about_movie(movie_name, field="genre")

        # flag = False
        # for pattern in what_genre:
        #     if re.search(pattern, question, re.IGNORECASE):
        #         flag = True
        # if flag:
        #     replies = [f"This movie can be attributed to {}."]
        #     return np.random.choice(replies)
        #
        # flag = False
        # for pattern in varity_genre:
        #     if re.search(pattern, question, re.IGNORECASE):
        #         flag = True
        # if flag:
        #     replies = [f"This movie can be attributed to {}."]
        #     return np.random.choice(replies)

        return ""

    @staticmethod
    def opinion_about_person(name, attitude, profession="actor"):
        """
        Generate templated reply about `name` with the given `attitude`
        """
        if attitude == "very_positive":
            replies = [f"I like {name} so much!",
                       f"I like {name} a lot!",
                       f"I love {name}!",
                       f"I adore {name}!",
                       f"{name} is my favorite {profession}!",
                       f"{name} is one of the best {profession}s!",
                       f"{name} is an awesome {profession}!",
                       f"{name} is a perfect {profession}!",
                       f"{name} is an outstanding {profession}!",
                       ]
            return np.random.choice(replies)
        if attitude == "positive":
            replies = [f"I like {name}.",
                       f"I think I like {name}.",
                       f"{name} is a nice {profession}.",
                       f"{name} is a good {profession}.",
                       f"{name} is a talented {profession}.",
                       f"{name} is a skilled {profession}.",
                       ]
            return np.random.choice(replies)
        if attitude == "neutral":
            replies = [f"I can't say whether I like {name} or not.",
                       f"Some people think {name} is a good {profession}.",
                       f"Probably {name} is a good {profession} for some people.",
                       f"{name} is a professional {profession}, so {name} deserves "
                       f"a good review from a professional bot."
                       ]
            return np.random.choice(replies)
        if attitude == "unknown":
            replies = [f"I have never heard about {name}.",
                       f"I don't know who {name} is.",
                       f"I don't know who is it.",
                       f"I can't say because I don't know who {name} is.",
                       f"I can't say because I have never heard about {name}."
                       ]
            return np.random.choice(replies)
        if attitude == "incorrect":
            article = "an" if profession == "actor" else "a"
            replies = [f"I've never heard that {name} worked as {article} {profession}.",
                       f"I'm not sure that {name} is {article} {profession}.",
                       ]
            return np.random.choice(replies)

    @staticmethod
    def opinion_about_movie(name, attitude, genres=[]):
        """
        Generate templated reply about movie `name` with the given `attitude`
        """
        subject = np.random.choice(["movie", "film", "pic", "picture"] + [genre.lower() + " movie" for genre in genres])

        if attitude == "very_positive":
            replies = [f"I like {name} so much!",
                       f"I like {name} a lot!",
                       f"I love {name}!",
                       f"I adore {name}!",
                       f"I like this {subject} so much!",
                       f"I like this {subject} a lot!",
                       f"I love this {subject}!",
                       f"I adore this {subject}!",
                       f"{name} is my favorite {subject}!",
                       f"{name} is one of the best {subject}s!",
                       f"{name} is an awesome {subject}!",
                       f"{name} is a perfect {subject}!",
                       f"{name} is an outstanding {subject}!",
                       ]
            return np.random.choice(replies)
        if attitude == "positive":
            replies = [f"I like {name}.",
                       f"I think I like {name}.",
                       f"{name} is a nice {subject}.",
                       f"{name} is a good {subject}.",
                       f"{name} is an interesting {subject}.",
                       ]
            return np.random.choice(replies)
        if attitude == "neutral":
            replies = [f"I can't say whether I like {name} or not.",
                       f"Some people think {name} is a good {subject}.",
                       f"Probably {name} is a good {subject} for some people."
                       ]
            return np.random.choice(replies)
        if attitude == "unseen":
            replies = [f"I have never heard about {name}.",
                       f"I have never heard about this {subject}.",
                       f"I have never seen {name}.",
                       f"I have never seen this {subject}.",
                       f"I don't know this {subject}."
                       ]
            return np.random.choice(replies)

    def give_opinion_about_persons_in_movie(self, movie_id, names, profession=None, attitude=None):
        """
        Generate templated reply about `names` in the given movie and attributes dictionary
        """
        movie = np.random.choice(
            ["this movie", "this film", "this pic", "this picture"] + [
                "this " + g.lower() + " movie" for g in self.imdb(movie_id)["genre"]] + [self.imdb(movie_id)["title"]])
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
                return (f"{opinion} Although I am not sure that {name} appeared in {movie}.",
                        {profession: [(name, attitude)]})

            if attitude is None:
                attitude = self.imdb.generate_opinion_about_movie_person(name, profession)

            if profession == "actor":
                article = "an"
            else:
                article = "a"

            if attitude == "very_positive":
                replies = [f"{name} gave their best as {article} {profession} in {movie}!",
                           f"{name} gave their best in {movie}!",
                           f"{name} showed their great potential in {movie}!",
                           f"{name} showed their talent as {article} {profession} in {movie}!",
                           ]
                return np.random.choice(replies), {profession: [(name, attitude)]}
            if attitude == "positive":
                replies = [f"{name} did a good work as {article} {profession} in {movie}.",
                           f"{name} worked hard in {movie}!",
                           f"{name} greatly contributed as {article} {profession} to {movie}!",
                           ]
                return np.random.choice(replies), {profession: [(name, attitude)]}
            if attitude == "neutral":
                replies = [f"{name} is one of the {profession}s of {movie}. "
                           f"But I can't say whether they did a good work or not.",
                           f"{name} as a professional {profession} deserves acknowledgment for work to {movie}!",
                           ]
                return np.random.choice(replies), {profession: [(name, attitude)]}
            if attitude == "unknown":
                replies = [f"I have never heard that {name} took part in {movie}.",
                           f"I didn't know that {name} was in {movie}.",
                           ]
                return np.random.choice(replies), {profession: [(name, attitude)]}
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
                    return (f"I suppose these guys are of different occupations in {movie}.",
                            {prof: [(name, "info")] for name, prof in zip(names, profession)})
                else:
                    # chose profession and go ahead
                    if "actor" in common_professions_in_this_movie:
                        profession = "actor"
                    else:
                        profession = common_professions_in_this_movie[0]
            else:
                professions = np.array([self.imdb.get_main_profession(name) for name in names])
                not_from_movie_names = ", ".join(np.array(names)[np.array(are_in_this_movie) is False])
                return (f"I suppose {not_from_movie_names} didn't participated in {movie}.",
                        {prof: [(name, "incorrect")]
                         for name, prof in zip(np.array(names)[np.array(are_in_this_movie) is False],
                                               np.array(professions)[np.array(are_in_this_movie) is False])})

            attitudes = []
            for name in names:
                attitudes += [self.imdb.generate_opinion_about_movie_person(name, profession)]

            if "very_positive" in attitudes and len(np.unique(attitudes)) == 1:
                replies = [f"They gave their best as {profession}s in {movie}!",
                           f"They gave their best in {movie}!",
                           f"They showed their great potential in {movie}!",
                           f"They showed their great talent as {profession}s in {movie}!",
                           ]
                return np.random.choice(replies), {profession: [(name, attitude)
                                                                for name, attitude in zip(names, attitudes)]}
            elif "very_positive" in attitudes and len(np.unique(attitudes)) > 1:
                # if at least one of the attitudes is `very_positive`
                # choose one of the names with this attitude as the best
                name = names[attitudes.index("very_positive")]
                replies = [f"They all did a good work in {movie} but {name} sunk into my soul.",
                           f"They worked hard. Although, {name} is one of my favourite {profession}s in {movie}.",
                           ]
                return np.random.choice(replies), {profession: [(name, attitude)
                                                                for name, attitude in zip(names, attitudes)]}
            elif "positive" in attitudes and len(np.unique(attitudes)) > 1:
                # if at least one of the attitudes is `positive` and noone is `very_positive`
                # choose one of the names with this attitude as the best
                name = names[attitudes.index("positive")]
                replies = [f"They are of the same high level {profession}s in {movie}.",
                           f"They deserve acknowledgment for their work in {movie}.",
                           ]
                return np.random.choice(replies), {profession: [(name, attitude)
                                                                for name, attitude in zip(names, attitudes)]}
            else:
                # either all `positive` or all `neutral`
                replies = [f"They all are good in {movie}.",
                           f"They are professional {profession}s, so they deserve credits for {movie}.",
                           ]
                return np.random.choice(replies), {profession: [(name, attitude)
                                                                for name, attitude in zip(names, attitudes)]}

    @staticmethod
    def donotknow():
        reaction = np.random.choice(["Hmm... ", "Sorry. "])

        replies = ["I don't who or what is it.",
                   "I don't know what are you talking about.",
                   "I have never heard about he, she or it.",
                   "I don't even understand who or what is it.",
                   ]
        return reaction + np.random.choice(replies)

    @staticmethod
    def didnotknowbefore():
        reaction = np.random.choice(["Hmm. ", "Wow! ", "Sounds interesting! ", "Uh. ", "Really? "])

        replies = ["I didn't know.",
                   "I didn't know that.",
                   "I didn't know that before.",
                   "I have never heard.",
                   "I have never heard about that.",
                   "I have never heard about that before."
                   "Thank you for information.",
                   "Thank you for information about that.",
                   ]
        return reaction + np.random.choice(replies)
