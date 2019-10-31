import json
import re
import string
import logging

import numpy as np
from ahocorapy.keywordtree import KeywordTree


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


class IMDb:
    professions = ["actor", "director"]

    def __init__(
            self,
            db_path="/home/dilyara/Documents/GitHub/dp-agent-alexa/skills/movie_skill/databases/imdb_dataset_58k.json"):
        """

        Args:
            db_path: path to the json database file
        """
        self.movies_names_tree = KeywordTree(case_insensitive=True, )
        self.names_tree = {}
        for prof in self.professions:
            self.names_tree[prof] = KeywordTree(case_insensitive=True)

        with open(db_path, "r") as f:
            # list of dictionaries. Each dictionary is about one movie
            self.database = json.load(f)

        # make the databases of the same structure
        if "imdb_id" in self.database[0].keys():
            if re.match("tt+", self.database[0]["imdb_id"]):
                for movie in self.database:
                    movie["imdb_id"] = movie["imdb_id"][2:]
            self.database = {movie["imdb_id"]: movie for movie in self.database}
        elif "imdb_url" in self.database[0].keys():
            for j in range(len(self.database)):
                for s in self.database[j]["imdb_url"].split("/"):
                    if re.match("tt+", s):
                        self.database[j]["imdb_id"] = s[2:]
                self.database[j]["imdb_rating"] = self.database[j]["users_rating"]
                self.database[j].pop("users_rating")
            self.database = {movie["imdb_id"]: movie for movie in self.database}

        # dictionary for getting imdb_id having name of the movie
        # these dictionaries of the same type: key `movie title` <-> value `imdb_id`
        self.movies_names = {self.database[imdb_id]["title"]: imdb_id
                             for imdb_id in self.database}
        self.lowercased_movies_names = {self.database[imdb_id]["title"].lower(): imdb_id
                                        for imdb_id in self.database}
        self.processed_movies_names = {self.process_movie_name(movie): self.movies_names[movie]
                                       for movie in self.movies_names.keys()}

        # let's get rid from movie `Movie`, `You` to escape many incorrect cases
        for title in ["Movie", "You", "Up", "She", "Shi", "Can", "Me2", "One", "If",
                      "In", "New", "He", "Why", "Two", "OK", "Em", "Out", "Me", "Yes", "It"]:
            movie_id = self.movies_names[title]
            self.database.pop(movie_id)
            self.movies_names.pop(title)
            self.lowercased_movies_names.pop(title.lower())
            self.processed_movies_names.pop(title.lower())

        # add lower-cased names of different professionals to the database
        for imdb_id in self.database:
            for profession in self.professions:
                if f"{profession}s" in self.database[imdb_id]:
                    self.database[imdb_id][f"lowercased_{profession}s"] = [
                        name.lower() for name in self.database[imdb_id][f"{profession}s"]]
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

        # compose trees
        # add whitespaces to find thise words only as tokens not as a part of other words
        for movie in self.processed_movies_names:
            self.movies_names_tree.add(f" {movie} ")
        self.movies_names_tree.finalize()

        for prof in self.professions:
            for person in self.professionals[f"lowercased_{prof}s"]:
                self.names_tree[prof].add(f" {person} ")
            self.names_tree[prof].finalize()

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
                 (r"\s?(part)?\s?II\s?", " part 2 "),
                 (r"\s?(part)?\s?III\s?", " part 3 "),
                 (r"\s?the first part\s?", " part 1 "),
                 (r"\s?the second part\s?", " part 2 "),
                 (r"\s?the third part\s?", " part 3 "),
                 (r"\s?the fourth part\s?", " part 4 "),
                 (r"\s?the fifth part\s?", " part 5 "),
                 (r"\s?the sixth part\s?", " part 6 "),
                 (r"\s?the seventh part\s?", " part 7 "),
                 (r"\s?the eighth part\s?", " part 8 "),
                 (r"\s?the ninth part\s?", " part 9 "),
                 ]

        movie_name = movie
        for pair in pairs:
            movie_name = re.sub(pair[0], pair[1], movie_name)
        puncts = string.punctuation
        for p in puncts:
            movie_name = movie_name.replace(p, " ")
        movie_name = re.sub(r"\s\s+", ' ', movie_name).strip()

        return movie_name.lower()

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
            return self.lowercased_movies_names[name.lower()]
        except KeyError:
            return None

    def get_info_about_movie(self, name: str, field="title"):
        """
        Return `field` value from the database given name (`title` or `imdb_id`) of the movie

        Args:
            name: title (could be lower-cased) or `imdb_id`
            field: for `imdb_dataset_58k.json`: 'title', 'rating', 'year', 'users_rating',
                                                'votes', 'metascore', 'img_url', 'countries',
                                                'languages', 'actors', 'genre', 'tagline',
                                                'description', 'directors', 'runtime', 'imdb_url'
                   for `imdb_top250.json`:      'title', 'year', 'rated', 'released', 'runtime',
                                                'genre', 'actors', 'plot', 'awards', 'poster',
                                                'ratings', 'metascore', 'imdb_rating', 'imdb_votes',
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

    def __call__(self, name_or_id):
        """
        Return the dictionary with all the available information about the given movie by `imdb_id` or `title`

        Args:
            name_or_id: imdb_id or movie title (could be lower-cased)

        Returns:
            dictionary
            empty dictionary if movie not in the database
        """
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

    def find_name(self, reply, subject="movie"):
        """
        Find name in the given reply (across preprocessed movies names from the database
        or lower-cased names of people of the given profession)

        Args:
            reply: any string reply
            subject: `movie`, `actor` or any profession

        Returns:
            imdb-ids if `movie`, full cased name if `actor` or any profession
        """
        lengths = []
        identifiers = []
        starts = []

        lower_cased_reply = f" {self.process_movie_name(reply.lower())} "
        if subject == "movie":
            results = self.movies_names_tree.search_all(lower_cased_reply)
        else:
            results = self.names_tree[subject].search_all(lower_cased_reply)

        bad_ids = []
        for result in results:
            # each result = ("name", start_index)
            found_substring = result[0]  # including whitespaces
            start = result[1]

            for i, length in enumerate(lengths):
                if len(found_substring) > length:
                    if start <= starts[i] < start + len(found_substring):
                        # e.g. found `Morgan` and `Morgan Freeman` -> let's get rid from Morgan
                        bad_ids.append(i)

            lengths.append(len(found_substring[1:-1]))  # exclude whitespaces
            if subject == "movie":
                found = self.processed_movies_names[found_substring[1:-1]]  # exclude whitespaces
            else:
                found = self.professionals[f"lowercased_{subject}s"][found_substring[1:-1]]  # exclude whitespaces

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

            if rating >= 8.0:
                return "very_positive"
            elif 8.0 > rating >= 6.0:
                return "positive"
            elif 6.0 > rating >= 5.0:
                return "neutral"
            else:
                return "unseen"

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

            if rating >= 6.5:
                return "very_positive"
            elif 6.5 > rating >= 6.0:
                return "positive"
            elif 6.0 > rating >= 5.0:
                return "neutral"
            else:
                return "unknown"
