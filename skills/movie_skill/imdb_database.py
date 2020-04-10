import json
import time
import re
import logging
import string
from copy import deepcopy
import pickle
from pathlib import Path

import numpy as np
from ahocorapy.keywordtree import KeywordTree
from nltk.tokenize import wordpunct_tokenize

from utils import GENRES, ALL_GENRES

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


class IMDb:
    professions = ["actor", "director"]

    def __init__(self, db_path="./databases/database_main_info.json", save_folder="../data/"):
        t0 = time.time()
        self.with_ignored_movies_names = {}
        self.without_ignored_movies_names = {}
        self.database = {}
        self.professionals = {}
        self.without_ignored_movies_names_tree = None
        self.with_ignored_movies_names_tree = None
        self.names_tree = None
        self.genres_tree = None

        if (Path(save_folder).joinpath(
                "with_ignored_movies_names.json").exists() and Path(save_folder).joinpath(
                "without_ignored_movies_names.json").exists() and Path(save_folder).joinpath(
                "database.json").exists() and Path(save_folder).joinpath(
                "professionals.json").exists() and Path(save_folder).joinpath(
                "without_ignored_movies_names_tree.pkl").exists() and Path(save_folder).joinpath(
                "with_ignored_movies_names_tree.pkl").exists() and Path(save_folder).joinpath(
                "names_tree.pkl").exists() and Path(save_folder).joinpath(
                "genres_tree.pkl").exists()):
            self.load(save_folder)
        else:
            self.train_and_save(db_path, save_folder)

        logger.info(f"Initialized in {time.time() - t0} sec")
        logger.info(f"Search across {len(self.with_ignored_movies_names)} with ignored movies")
        logger.info(f"Search across {len(self.without_ignored_movies_names)} without ignored movies")
        npersons = 0
        for prof in self.professions:
            for person in self.professionals[f"lowercased_{prof}s"]:
                if len(person.split()) > 1:
                    npersons += 1
        logger.info(f"Search across {npersons} persons names")

    def save(self, save_folder):
        with open(Path(save_folder).joinpath("with_ignored_movies_names.json"), "w") as f:
            json.dump(self.with_ignored_movies_names, f, indent=2)

        with open(Path(save_folder).joinpath("without_ignored_movies_names.json"), "w") as f:
            json.dump(self.without_ignored_movies_names, f, indent=2)

        with open(Path(save_folder).joinpath("database.json"), "w") as f:
            json.dump(self.database, f, indent=2)

        with open(Path(save_folder).joinpath("professionals.json"), "w") as f:
            json.dump(self.professionals, f, indent=2)

        with open(Path(save_folder).joinpath("without_ignored_movies_names_tree.pkl"), "wb") as f:
            pickle.dump(self.without_ignored_movies_names_tree, f)

        with open(Path(save_folder).joinpath("with_ignored_movies_names_tree.pkl"), "wb") as f:
            pickle.dump(self.with_ignored_movies_names_tree, f)

        with open(Path(save_folder).joinpath("names_tree.pkl"), "wb") as f:
            pickle.dump(self.names_tree, f)

        with open(Path(save_folder).joinpath("genres_tree.pkl"), "wb") as f:
            pickle.dump(self.genres_tree, f)

    def load(self, save_folder):
        start_time = time.time()
        logger.info(f"Loading models")
        with open(Path(save_folder).joinpath("with_ignored_movies_names.json"), "r") as f:
            self.with_ignored_movies_names = json.load(f)

        with open(Path(save_folder).joinpath("without_ignored_movies_names.json"), "r") as f:
            self.without_ignored_movies_names = json.load(f)

        with open(Path(save_folder).joinpath("database.json"), "r") as f:
            self.database = json.load(f)

        with open(Path(save_folder).joinpath("professionals.json"), "r") as f:
            self.professionals = json.load(f)

        with open(Path(save_folder).joinpath("without_ignored_movies_names_tree.pkl"), "rb") as f:
            self.without_ignored_movies_names_tree = pickle.load(f)

        with open(Path(save_folder).joinpath("with_ignored_movies_names_tree.pkl"), "rb") as f:
            self.with_ignored_movies_names_tree = pickle.load(f)

        with open(Path(save_folder).joinpath("names_tree.pkl"), "rb") as f:
            self.names_tree = pickle.load(f)

        with open(Path(save_folder).joinpath("genres_tree.pkl"), "rb") as f:
            self.genres_tree = pickle.load(f)

        logger.info(f"Loading models time {time.time() - start_time}")

    def train_and_save(self, db_path, save_folder):
        t0 = time.time()
        self.without_ignored_movies_names_tree = KeywordTree(case_insensitive=True)
        self.with_ignored_movies_names_tree = KeywordTree(case_insensitive=True)
        self.genres_tree = KeywordTree(case_insensitive=True)
        self.names_tree = {}
        for prof in self.professions:
            self.names_tree[prof] = KeywordTree(case_insensitive=True)

        with open(db_path, "r") as f:
            self.database = json.load(f)

        if "imdb_id" in self.database[0].keys():
            self.database = [movie for movie in self.database if movie]
            if re.match("tt+", self.database[0]["imdb_id"]):
                for movie in self.database:
                    movie["imdb_id"] = movie["imdb_id"][2:]
            for movie in self.database:
                movie["imdb_rating"] = float(movie["imdb_rating"])
            self.database = {movie["imdb_id"]: movie for movie in self.database}
        elif "imdb_url" in self.database[0].keys():
            for j in range(len(self.database)):
                for s in self.database[j]["imdb_url"].split("/"):
                    if re.match("tt+", s):
                        self.database[j]["imdb_id"] = s[2:]
                try:
                    self.database[j]["imdb_rating"] = float(self.database[j]["users_rating"])
                except TypeError:
                    self.database[j]["imdb_rating"] = 0.0
                self.database[j].pop("users_rating")
            self.database = {movie["imdb_id"]: movie for movie in self.database}

        self.movies_names = {}
        for imdb_id in self.database:
            self.movies_names[self.database[imdb_id]["title"]] = []
        for imdb_id in self.database:
            self.movies_names[self.database[imdb_id]["title"]].append(imdb_id)

        self.without_ignored_movies_names = {self.process_movie_name(movie): self.movies_names[movie]
                                             for movie in self.movies_names.keys()}
        self.with_ignored_movies_names = deepcopy(self.without_ignored_movies_names)

        with open("databases/google-10000-english-no-swears.txt", "r") as f:
            self.frequent_unigrams = f.read().splitlines()[:5000]

        with open("databases/w2_.txt", "r", encoding="cp1251") as f:
            bigrams = f.read().splitlines()

        for i in range(len(bigrams)):
            bigrams[i] = bigrams[i].split("\t")
        self.frequent_bigrams = []
        for bigram in bigrams:
            if int(bigram[0]) > 1000 and "a" not in bigram and "the" not in bigram:
                self.frequent_bigrams.append(bigram[1] + " " + bigram[2])

        movie_titles_to_ignore = self.get_processed_movies_titles_to_ignore()
        for proc_title in movie_titles_to_ignore:
            try:
                self.without_ignored_movies_names.pop(proc_title)
            except KeyError:
                pass
        for proc_title in ["movie", "tragedy", "favorite", "favourite", "angela",
                           "attitude", "do you believe", "earthquake", "gays",
                           "no matter what", "talk to me", "you", "lets talk",
                           "lets chat", "in", "if", "can", "o", "ok", "one",
                           "two", "film", "new", "next", "out", "love",
                           "like", "watch", "actress", "less", "want", "abortion",
                           "alexa", "you tell me", "movie movie", "tricks", "movies",
                           "yes", "action", "i", "maybe", "do you know", "isolation",
                           "something", 'no', 'i am', "what", "is", "it", "what",
                           "i did not know that", "cage", "bean", "back", "games",
                           "stronger", "see", "really"
                           ]:
            try:
                self.with_ignored_movies_names.pop(proc_title)
            except KeyError:
                pass
            try:
                self.without_ignored_movies_names.pop(proc_title)
            except KeyError:
                pass
        to_remove = []
        for proc_title in self.with_ignored_movies_names.keys():
            if re.match(f"^[{string.digits}]+$", proc_title):
                to_remove.append(proc_title)
        for proc_title in to_remove:
            self.with_ignored_movies_names.pop(proc_title)
            self.without_ignored_movies_names.pop(proc_title)

        # add lower-cased names of different professionals to the database
        for imdb_id in self.database:
            for profession in self.professions:
                if f"{profession}s" in self.database[imdb_id]:
                    self.database[imdb_id][f"lowercased_{profession}s"] = [
                        name.lower() for name in self.database[imdb_id][f"{profession}s"]
                        if len(name.split()) > 1]
                else:
                    self.database[imdb_id][f"lowercased_{profession}s"] = []
                    self.database[imdb_id][f"{profession}s"] = []

        # `self.professionals` is a dictionary with keys from `self.professions`
        # and ['lowercased_prof` for prof in `self.professions`].
        # Each field is a dictionary where key is a name of person and value is a list of movies imdb_ids
        # where this person was participating in the given profession.
        self.professionals = {}
        for prof in self.professions:
            self.collect_persons_and_movies(profession=prof)

        logger.info(f"Everything's except trees were done in {time.time() - t0} sec")

        # compose trees
        # add whitespaces to find thise words only as tokens not as a part of other words
        for movie in self.without_ignored_movies_names:
            self.without_ignored_movies_names_tree.add(f" {movie} ")
        self.without_ignored_movies_names_tree.finalize()

        for movie in self.with_ignored_movies_names:
            self.with_ignored_movies_names_tree.add(f" {movie} ")
        self.with_ignored_movies_names_tree.finalize()

        for prof in self.professions:
            for person in self.professionals[f"lowercased_{prof}s"]:
                if len(person.split()) > 1:
                    self.names_tree[prof].add(f" {person} ")
            self.names_tree[prof].finalize()

        # genres without whitespaces to include subwording genres
        self.genres_tree.add("genre")
        for genre in ALL_GENRES:
            self.genres_tree.add(f"{genre}")
        self.genres_tree.finalize()
        logger.info(f"Trained in {time.time() - t0} sec")
        self.save(save_folder)

    @staticmethod
    def process_movie_name(movie):
        """
        Process given string (which is mostly about movie names), lowercases,
        removes punctuation from title

        Args:
            movie: movie title

        Returns:

        """
        pairs = [(r"\s?\-\s?", " "),
                 (r"\s?\+\s?", " plus "),
                 (r"\s?\*\s?", " star "),
                 (r"\s?\&\s?", " and "),
                 (r"\s?\'\s?", ""),
                 (r"\s?:\s?", ""),
                 (r"\s?ii\s?", " 2 "),
                 (r"\s?iii\s?", " 3 "),
                 (r"\s?II\s?", " 2 "),
                 (r"\s?III\s?", " 3 "),
                 (r"\s?IV\s?", " 4 "),
                 (r"\s?V\s?", " 5 "),
                 (r"\s?VI\s?", " 6 "),
                 (r"\s?VII\s?", " 7 "),
                 (r"\s?VII\s?", " 8 "),
                 (r"\s?IX\s?", " 9 "),
                 (r"\s?(the)?\s?first part\s?", " part 1 "),
                 (r"\s?(the)?\s?second part\s?", " part 2 "),
                 (r"\s?(the)?\s?third part\s?", " part 3 "),
                 (r"\s?(the)?\s?fourth part\s?", " part 4 "),
                 (r"\s?(the)?\s?fifth part\s?", " part 5 "),
                 (r"\s?(the)?\s?sixth part\s?", " part 6 "),
                 (r"\s?(the)?\s?seventh part\s?", " part 7 "),
                 (r"\s?(the)?\s?eighth part\s?", " part 8 "),
                 (r"\s?(the)?\s?ninth part\s?", " part 9 "),
                 (r"\s?(the)?\s?first\s?", " part 1 "),
                 (r"\s?(the)?\s?second\s?", " part 2 "),
                 (r"\s?(the)?\s?third\s?", " part 3 "),
                 (r"\s?(the)?\s?fourth\s?", " part 4 "),
                 (r"\s?(the)?\s?fifth\s?", " part 5 "),
                 (r"\s?(the)?\s?sixth\s?", " part 6 "),
                 (r"\s?(the)?\s?seventh\s?", " part 7 "),
                 (r"\s?(the)?\s?eighth\s?", " part 8 "),
                 (r"\s?(the)?\s?ninth\s?", " part 9 "),
                 (r"\s+the\s+", " "),
                 (r"\s+a\s+", " "),
                 (r"^the\s+", ""),
                 (r"^a\s+", ""),
                 (r"\s+the$", ""),
                 (r"\s+a$", ""),
                 ]

        movie_name = movie.lower()
        for pair in pairs:
            movie_name = re.sub(pair[0], pair[1], movie_name)
        puncts = string.punctuation
        for p in puncts:
            movie_name = movie_name.replace(p, " ")
        movie_name = re.sub(r"\s\s+", ' ', movie_name).strip()

        return movie_name

    def get_processed_movies_titles_to_ignore(self):
        to_ignore = list(set(self.without_ignored_movies_names.keys()).intersection(
            set(self.frequent_unigrams + self.frequent_bigrams)))

        return to_ignore

    def collect_persons_and_movies(self, profession="actor"):

        self.professionals[f"{profession}s"] = {}
        self.professionals[f"lowercased_{profession}s"] = {}

        for imdb_id in self.database:
            for name in self.database[imdb_id][f"{profession}s"]:
                if name in self.professionals[f"{profession}s"].keys():
                    self.professionals[f"{profession}s"][name] += [imdb_id]
                else:
                    self.professionals[f"{profession}s"][name] = [imdb_id]
                    self.professionals[f"lowercased_{profession}s"][name.lower()] = name

    def get_movie_name(self, imdb_id):
        """
        Given `imdb_id` of the movie return its title (cased)

        Args:
            imdb_id: identification string from IMDb

        Returns:
            movie title (cased)
            None if the movie not in the database
        """
        try:
            return self.database[imdb_id]["title"]
        except KeyError:
            return None

    def get_imdb_id(self, name):
        """
        Given title of the movie return its `imdb_id`

        Args:
            name: movie title (could be lower-cased)

        Returns:
            movie `imdb_id`
            None if the movie not in the database
        """
        try:
            return self.get_imdb_id_based_only_on_title(name)
        except KeyError:
            return None

    def get_imdb_id_based_only_on_title(self, name):
        """
        Given title of the movie return its `imdb_id`.
        If several movies with the same title, choose those with the highest rating

        Args:
            name: movie title (could be lower-cased)

        Returns:
            movie `imdb_id`
            None if the movie not in the database
        """
        imdb_ids = self.with_ignored_movies_names.get(self.process_movie_name(name), None)
        if imdb_ids is None:
            return None
        elif len(imdb_ids) == 1:
            return imdb_ids[0]
        else:
            highest_rating = 0.
            best_imdb_id = imdb_ids[0]
            for imdb_id in imdb_ids:
                rating = self.database[imdb_id].get("imdb_rating", None)
                if rating is None:
                    continue
                else:
                    if rating > highest_rating:
                        highest_rating = rating
                        best_imdb_id = imdb_id
            return best_imdb_id

    def get_info_about_movie(self, name: str, field="title"):
        """
        Return `field` value from the database given name (`title` or `imdb_id`) of the movie

        Args:
            name: title (could be lower-cased) or `imdb_id`
            field: for `imdb_dataset_58k.json`: 'title', 'rating', 'year', 'imdb_rating',
                                                'votes', 'metascore', 'img_url', 'countries',
                                                'languages', 'actors', 'genre', 'tagline',
                                                'description', 'directors', 'runtime', 'imdb_url'
                   for `imdb_top250.json`:      'title', 'year', 'rated', 'released', 'runtime',
                                                'genre', 'actors', 'plot', 'awards', 'poster',
                                                'imdb_rating', 'metascore', 'imdb_rating', 'imdb_votes',
                                                'imdb_id', 'type',  'tomato_url', 'dvd', 'box_office',
                                                'production', 'website', 'response', 'writers',
                                                'directors', 'languages', 'countries'

        Returns:
            `field` value from the database
            None if movie not in the database or key `field` not in the movie description dictionary
        """
        try:
            return self.__call__(name)[field]
        except KeyError:
            return None

    def get_main_profession(self, name: str, from_which_professions=None):
        max_movies = 0
        profession = "actor"

        if from_which_professions is None:
            from_which_professions = self.professions

        for prof in from_which_professions:
            try:
                n_movies = len(self.professionals[f"{prof}s"][name])
            except KeyError:
                n_movies = 0
            if n_movies > max_movies:
                max_movies = n_movies
                profession = prof

        return profession

    def __call__(self, name_or_id):
        """
        Return the dictionary with all the available information about the given movie by `imdb_id` or `title`

        Args:
            name_or_id: imdb_id or movie title (could be lower-cased)

        Returns:
            dictionary
            empty dictionary if movie not in the database
        """
        if name_or_id is None:
            return {}

        if name_or_id.isdigit() and 6 <= len(name_or_id) <= 8:
            # this is imdb_id
            pass
        else:
            # this is a string name
            name_or_id = self.get_imdb_id(name_or_id)
        try:
            return self.database[name_or_id]
        except KeyError:
            # exception if name_or_id == None or name_or_id not in database
            return {}

    def find_name(self, reply, subject="movie", find_ignored=False):
        """
        Find name in the given reply (across preprocessed movies names from the database
        or lower-cased names of people of the given profession)

        Args:
            reply: any string reply
            subject: `movie`, `actor` or any profession, `genre`
            find_ignored: whether to search among ignored movies titles

        Returns:
            imdb-ids if `movie`, full cased name if `actor` or any profession
        """
        lengths = []
        identifiers = []
        starts = []

        lower_cased_reply = f" {self.process_movie_name(reply.lower())} "
        if subject == "movie":
            results = self.without_ignored_movies_names_tree.search_all(lower_cased_reply)
            results = list(results)
            if find_ignored:
                results = self.with_ignored_movies_names_tree.search_all(lower_cased_reply)
            elif len(results) == 0:
                for target_name in ["film", "series", "movie"]:
                    start_movie_name = reply.lower().find(target_name)
                    if start_movie_name != -1:
                        if lower_cased_reply[-(len(target_name) + 1):] == f"{target_name} ":
                            tokens = wordpunct_tokenize(lower_cased_reply)
                            new_lower_cased_reply = f" {self.process_movie_name(' '.join(tokens[-3:]))} "
                            logger.info(f"1. Trying to find movie title in `{new_lower_cased_reply}`")
                            results = self.with_ignored_movies_names_tree.search_all(new_lower_cased_reply)
                        else:
                            tokens = wordpunct_tokenize(reply[start_movie_name:])
                            new_lower_cased_reply = f" {self.process_movie_name(' '.join(tokens[:3]))} "
                            logger.info(f"2. Trying to find movie title in `{new_lower_cased_reply}`")
                            results = self.with_ignored_movies_names_tree.search_all(new_lower_cased_reply)

        elif subject in self.professions:
            results = self.names_tree[subject].search_all(lower_cased_reply)
        elif subject == "genre":
            results = self.genres_tree.search_all(lower_cased_reply)
        else:
            results = []

        results = list(results)
        bad_ids = []
        for result in results:
            # each result = ("name", start_index)
            found_substring = result[0]  # including whitespaces for `movie` and professions
            start = result[1]

            for i, length in enumerate(lengths):
                if len(found_substring) > length:
                    if start <= starts[i] < start + len(found_substring):
                        # e.g. found `Morgan` and `Morgan Freeman` -> let's get rid from Morgan
                        bad_ids.append(i)

            if found_substring[0] == " ":
                lengths.append(len(found_substring[1:-1]))  # exclude whitespaces
            else:
                lengths.append(len(found_substring))  # where no whitespaces - `genre`
            if subject == "movie":
                # found = self.with_ignored_movies_names[found_substring[1:-1]]  # exclude whitespaces
                found = self.get_imdb_id(found_substring[1:-1])  # exclude whitespaces
            elif subject in self.professions:
                found = self.professionals[f"lowercased_{subject}s"][found_substring[1:-1]]  # exclude whitespaces
            elif subject == "genre":
                for genre in GENRES:
                    if found_substring in GENRES[genre]:
                        found = genre  # cased genre title
            else:
                found = ""

            identifiers.append(found)
            starts.append(start)

        if len(lengths) == 0:
            return []
        else:
            lengths = np.array(lengths)
            identifiers = np.array(identifiers)
            lengths = np.delete(lengths, list(set(bad_ids)))
            identifiers = np.delete(identifiers, list(set(bad_ids)))

            if len(lengths) <= 3:
                return identifiers
            else:
                return []

    def get_movie_type(self, movie_id):
        curr_genres = self.__call__(movie_id).get("genre", [""])
        curr_genres = [g.lower() for g in curr_genres]
        if "show" in " ".join(curr_genres).lower():
            return "show"
        elif "animation" in curr_genres:
            return "animation"
        elif "series" in curr_genres:
            return "series"
        else:
            return "movie"

    def generate_opinion_about_movie(self, name: str):
        """
        Generate opinion about movie using database `imdb_rating`

        Args:
            name: movie title or `imdb_id`

        Returns:
            "very_positive" if movie `imdb_rating` >= 8.0
            "positive" if movie `imdb_rating` >= 6.0
            "neutral" if movie `imdb_rating` >= 5.0
            "unseen" if movie `imdb_rating` < 5.0
            None if movie not in the database
        """
        rating = self.get_info_about_movie(name, "imdb_rating")
        if rating is None:
            return None
        else:
            rating = float(rating)

            if rating >= 7.5:
                return "very_positive"
            elif rating >= 6.0:
                return "positive"
            else:
                return "neutral"

    def get_movies_with_person(self, name, profession="actor"):
        """
        Collect all the movies with the given person in the given profession.

        Args:
            name: person name (could be lower-cased)
            profession: `actor`, `director` or `writer` (if `writer` field in the database)

        Returns:
            list of `imdb_id` of movies with the given person in the given profession
        """
        movies = []
        for imdb_id in self.database:
            if name.lower() in self.database[imdb_id][f"lowercased_{profession}s"]:
                movies.append(imdb_id)
        return movies

    def generate_opinion_about_movie_person(self, name: str, profession="actor"):
        """
        Generate opinion about movie actor, director or writer (if `writer` field in the database).
        Collect all the movies with the given person in the given profession field,
        calculate average rating of these movies and return opinion depending on it.

        Args:
            name: person name (could be lower-cased)
            profession: `actor`, `director` or `writer` (if `writer` field in the database)

        Returns:
            "very_positive" if movie `imdb_rating` >= 6.0
            "positive" if movie `imdb_rating` >= 5.0
            "neutral" if movie `imdb_rating` >= 4.0
            "unseen" if movie `imdb_rating` < 4.0
            None if no movies with this person in this profession in the database
        """
        movies = self.get_movies_with_person(name, profession)

        if len(movies) == 0:
            return None
        else:
            rating = np.mean([float(self.get_info_about_movie(imdb_id, "imdb_rating")) for imdb_id in movies])

            if rating >= 7.75:
                return "very_positive"
            elif rating >= 7.0:
                return "positive"
            else:
                return "neutral"

    def genereate_opinion_about_genre(self, genre: str, attitude=None):
        """
        Return opinion about known genres and return genres of particular opinion.

        Args:
            genre: one of the known IMDb genres or `Genre`
            attitude: if `Genre` and `attitude` is given return genres with the given attitude

        Returns:
            string attitude if `attitude` is not given
            list of genres if `attitude` is given
        """
        genres = {
            # "Genre": ["I like comedies a lot. I also love different science fiction and documentary movies."],
            "Action": "positive",
            "Adult": "neutral",
            "Adventure": "positive",
            "Animation": "neutral",
            "Biography": "neutral",
            "Comedy": "very_positive",
            "Crime": "positive",
            "Documentary": "very_positive",
            "Drama": "neutral",
            "Family": "positive",
            "Fantasy": "positive",
            "Film-noir": "negative",
            "Game-show": "neutral",
            "History": "positive",
            "Horror": "neutral",
            "Music": "negative",
            "Musical": "negative",
            "Mystery": "negative",
            "News": "positive",
            "Reality-tv": "neutral",
            "Romance": "positive",
            "Sci-fi": "very_positive",
            "Short": "neutral",
            "Sport": "positive",
            "Talk-show": "positive",
            "Thriller": "neutral",
            "War": "neutral",
            "Western": "positive"
        }
        if genre == "Genre":
            if not(attitude is None):
                res = []
                for k in genres:
                    if genres[k] == attitude:
                        res += [k]
                return res
            else:
                return []
        else:
            return genres[genre]
