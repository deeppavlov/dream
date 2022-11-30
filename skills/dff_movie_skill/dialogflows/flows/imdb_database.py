import json
import time
import re
import logging

import numpy as np

from dialogflows.flows.utils import GENRES, ALL_GENRES

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


class IMDb:
    professions = ["actor", "director"]

    pairs = [
        (re.compile(r"\s?\-\s?"), " "),
        (re.compile(r"\s?\+\s?"), " plus "),
        (re.compile(r"\s?\*\s?"), " star "),
        (re.compile(r"\s?\&\s?"), " and "),
        (re.compile(r"\s?\'\s?"), " "),
        (re.compile(r"\s?:\s?"), " "),
        (re.compile(r"\bii\b"), "2"),
        (re.compile(r"\biii\b"), "3"),
        (re.compile(r"\bII\b"), "2"),
        (re.compile(r"\bIII\b"), "3"),
        (re.compile(r"\bIV\b"), "4"),
        (re.compile(r"\bV\b"), "5"),
        (re.compile(r"\bVI\b"), "6"),
        (re.compile(r"\bVII\b"), "7"),
        (re.compile(r"\bVII\b"), "8"),
        (re.compile(r"\bIX\b"), "9"),
        (re.compile(r"\bfirst part\b"), "part 1"),
        (re.compile(r"\bsecond part\b"), "part 2"),
        (re.compile(r"\bthird part\b"), "part 3"),
        (re.compile(r"\bfourth part\b"), "part 4"),
        (re.compile(r"\bfifth part\b"), "part 5"),
        (re.compile(r"\bsixth part\b"), "part 6"),
        (re.compile(r"\bseventh part\b"), "part 7"),
        (re.compile(r"\beighth part\b"), "part 8"),
        (re.compile(r"\bninth part\b"), "part 9"),
        (re.compile(r"\bthe\b"), ""),
        (re.compile(r"\ba\b"), ""),
        (re.compile(r"\ban\b"), ""),
        (re.compile(r"\W"), " "),
        (re.compile(r"\bvs\b"), "versus"),
        (re.compile(r"\bv\b"), "versus"),
        (re.compile(r"\s\s+"), " "),
    ]

    number_pairs = [
        (re.compile(r"\b1\b"), "one"),
        (re.compile(r"\b2\b"), "two"),
        (re.compile(r"\b3\b"), "three"),
        (re.compile(r"\b4\b"), "four"),
        (re.compile(r"\b5\b"), "five"),
        (re.compile(r"\b6\b"), "six"),
        (re.compile(r"\b7\b"), "seven"),
        (re.compile(r"\b8\b"), "eight"),
        (re.compile(r"\b9\b"), "nine"),
    ]

    def __init__(self, db_path="./databases/database_most_popular_main_info.json"):
        t0 = time.time()
        self.database = {}
        self.professionals = {}
        self.preprocessed_original = {}
        self.preprocessed_alternative = {}
        self.genres_pattern = None
        self.names_pattern = {}

        self.create_database(db_path)

        logger.info(f"Initialized in {time.time() - t0} sec")
        logger.info(f"Search across {len(self.preprocessed_original)} original movie titles")
        logger.info(f"Search across {len(self.preprocessed_alternative)} alternative movie titles")
        npersons = 0
        for prof in self.professions:
            for person in self.professionals[f"lowercased_{prof}s"]:
                if len(person.split()) > 1:
                    npersons += 1
        logger.info(f"Search across {npersons} persons names")

    def create_database(self, db_path):
        t0 = time.time()
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

        # dictionary mapping movie title to list of imdb ids
        self.movies_names = {}
        # dictionary mapping movie title to processed movie title for internal usage ONLY
        self.preprocessed_movies_names = {}

        for imdb_id in self.database:
            self.movies_names[self.database[imdb_id]["title"]] = []
        for imdb_id in self.database:
            movie_title = self.database[imdb_id]["title"]
            self.movies_names[movie_title].append(imdb_id)
            self.preprocessed_movies_names[movie_title] = self.process_movie_name(movie_title)
            for alt_title in self.database[imdb_id].get("all_titles", []):
                self.preprocessed_movies_names[alt_title] = self.process_movie_name(alt_title)

        # dictionary mapping processed ORIGINAL movie title to list of imdb ids of movies
        self.preprocessed_original = {
            self.preprocessed_movies_names.get(movie, ""): []
            for movie in self.movies_names.keys()
            if self.preprocessed_movies_names.get(movie, "")
        }
        # dictionary mapping processed ALTERNATIVE movie title to list of imdb ids of movies
        self.preprocessed_alternative = {}

        for imdb_id in self.database:
            movie = self.database[imdb_id]["title"]
            prep_movie = self.preprocessed_movies_names.get(movie, "")
            if prep_movie:
                self.preprocessed_original[prep_movie] += [imdb_id]

            for alt_title in self.database[imdb_id].get("all_titles", []):
                prev_al_title = self.preprocessed_movies_names.get(alt_title, "")
                if prev_al_title and prev_al_title in self.preprocessed_alternative:
                    self.preprocessed_alternative[self.preprocessed_movies_names[alt_title]] += [imdb_id]
                elif prev_al_title:
                    self.preprocessed_alternative[self.preprocessed_movies_names[alt_title]] = [imdb_id]

        with open("databases/google-10000-english-no-swears.txt", "r") as f:
            self.frequent_unigrams = f.read().splitlines()[:2000]
        self.frequent_unigrams.remove("up")  # very popular movie, let's leave it in our database

        # TOTALLY REMOVED MOVIES
        for proc_title in [
            "movie",
            "tragedy",
            "favorite",
            "favourite",
            "attitude",
            "do you believe",
            "no matter what",
            "talk to me",
            "you",
            "lets talk",
            "lets chat",
            "in",
            "if",
            "can",
            "o",
            "ok",
            "one",
            "two",
            "film",
            "new",
            "next",
            "out",
            "love",
            "like",
            "watch",
            "actress",
            "less",
            "want",
            "alexa",
            "you tell me",
            "movie movie",
            "movies",
            "yes",
            "action",
            "i",
            "maybe",
            "do you know",
            "something",
            "no",
            "i am",
            "what",
            "is",
            "it",
            "what",
            "i did not know that",
            "games",
            "see",
            "really",
            "my favorite movie",
            "i do",
            "what happened",
            "me",
            "off",
            "nothing",
            "talk to her",
            "boy a",
            "play",
            "i feel",
            "question",
            "thank you",
            "singing",
            "program",
            "other",
            "lets talk about",
            "conversation",
            "good",
            "they",
            "hello",
            "make",
            "pretty good",
            "talk",
            "ok",
            "okay",
            "tell me something",
            "different",
            "day",
            "seen",
            "i like",
            "wij",
            "because",
            "me too",
            "horror",
            "will",
            "character",
            "more",
            "show",
            "coming out",
            "remember",
            "again",
            "time",
            "news",
            "comics",
            "life",
            "playing",
            "weekend",
            "gays",
            "live",
            "travelling",
            "abortion",
            "foster",
            "kites",
        ]:
            try:
                self.preprocessed_original.pop(proc_title)
                self.preprocessed_alternative.pop(proc_title)
            except KeyError:
                pass
            try:
                self.preprocessed_original.pop(proc_title)
                self.preprocessed_alternative.pop(proc_title)
            except KeyError:
                pass
        to_remove = []
        for proc_title in self.preprocessed_original.keys():
            if re.match("^[0-9 ]+$", proc_title):
                to_remove.append(proc_title)
        for proc_title in to_remove:
            self.preprocessed_original.pop(proc_title)
        to_remove = []
        for proc_title in self.preprocessed_alternative.keys():
            if re.match("^[0-9 ]+$", proc_title):
                to_remove.append(proc_title)
        for proc_title in to_remove:
            self.preprocessed_alternative.pop(proc_title)

        # add lower-cased names of different professionals to the database
        for imdb_id in self.database:
            for profession in self.professions:
                if f"{profession}s" in self.database[imdb_id]:
                    self.database[imdb_id][f"lowercased_{profession}s"] = [
                        self.process_person_name(name)
                        for name in self.database[imdb_id][f"{profession}s"]
                        if len(name.split()) > 1
                    ]
                else:
                    self.database[imdb_id][f"lowercased_{profession}s"] = []
                    self.database[imdb_id][f"{profession}s"] = []
            # self.database[imdb_id]["characters"] = [
            #     json.loads(char_list)[0]
            #     for char_list in self.database[imdb_id]["characters"] if json.loads(char_list)
            # ]
        # `self.professionals` is a dictionary with keys from `self.professions`
        # and ['lowercased_prof` for prof in `self.professions`].
        # Each field is a dictionary where key is a name of person and value is a list of movies imdb_ids
        # where this person was participating in the given profession.
        self.professionals = {}
        for prof in self.professions:
            self.collect_persons_and_movies(profession=prof)

        logger.info(f"Everything's except patterns were done in {time.time() - t0} sec")

        for prof in self.professions:
            self.names_pattern[prof] = re.compile(
                "(" + "|".join([r"\b%s\b" % name for name in self.professionals[f"lowercased_{prof}s"]]) + ")",
                re.IGNORECASE,
            )
        self.genres_pattern = re.compile("(" + "|".join([r"\b%s" % genre for genre in ALL_GENRES]) + ")", re.IGNORECASE)

        logger.info(f"Created db in {time.time() - t0} sec")

    def process_movie_name(self, movie):
        movie_name = movie.lower()
        for pair in self.pairs:
            movie_name = re.sub(pair[0], pair[1], movie_name)
        return movie_name.strip()

    def process_numbers_in_movie_name(self, movie):
        movie_name = movie.lower()
        for pair in self.number_pairs:
            movie_name = re.sub(pair[0], pair[1], movie_name)
        return movie_name.strip()

    def process_person_name(self, name):
        name = name.lower()
        for pair in self.pairs[-2:]:
            name = re.sub(pair[0], pair[1], name)
        return name.strip()

    def get_processed_movies_titles_to_ignore(self):
        to_ignore = list(
            set(self.preprocessed_original.keys()).intersection(set(self.frequent_unigrams + self.frequent_bigrams))
        )
        to_ignore += list(
            set(self.preprocessed_alternative.keys()).intersection(set(self.frequent_unigrams + self.frequent_bigrams))
        )

        return to_ignore

    def collect_persons_and_movies(self, profession="actor"):

        self.professionals[f"{profession}s"] = {}
        self.professionals[f"lowercased_{profession}s"] = {}

        for imdb_id in self.database:
            for name in self.database[imdb_id][f"{profession}s"]:
                if len(name.split()) > 1:
                    if name in self.professionals[f"{profession}s"].keys():
                        self.professionals[f"{profession}s"][name] += [imdb_id]
                    else:
                        self.professionals[f"{profession}s"][name] = [imdb_id]
                        self.professionals[f"lowercased_{profession}s"][self.process_person_name(name)] = name

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
        If several movies with the same title, choose those with the highest numVotes

        Args:
            name: movie title (could be lower-cased)

        Returns:
            movie `imdb_id`
            None if the movie not in the database
        """
        processed_movie_title = self.process_movie_name(name)
        preprocessed_original_title_ids = self.preprocessed_original.get(processed_movie_title, None)
        preprocessed_alternative_title_ids = self.preprocessed_alternative.get(processed_movie_title, None)

        imdb_ids = preprocessed_original_title_ids if preprocessed_original_title_ids else []
        imdb_ids += preprocessed_alternative_title_ids if preprocessed_alternative_title_ids else []

        if imdb_ids is None or len(imdb_ids) == 0:
            return None
        elif len(imdb_ids) == 1:
            return imdb_ids[0]
        else:
            highest_numvotes = 0
            best_imdb_id = imdb_ids[0]
            for imdb_id in imdb_ids:
                numvotes = self.get_info_about_movie(imdb_id, "numVotes")
                if numvotes is None:
                    continue
                else:
                    if numvotes > highest_numvotes:
                        highest_numvotes = numvotes
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

        if name_or_id.isdigit() and 6 <= len(name_or_id):
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

    def find_name(self, reply, subject="movie", find_ignored=False, return_longest=True):
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
        lower_cased_reply = f" {self.process_movie_name(reply.lower())} "

        if subject in self.professions:
            results = re.findall(self.names_pattern[subject], lower_cased_reply)
        elif subject == "genre":
            results = re.findall(self.genres_pattern, lower_cased_reply)
        else:
            results = []

        results = list(results)
        identifiers = []
        for result in results:
            found = ""
            if subject in self.professions:
                found = self.professionals[f"lowercased_{subject}s"][result]
            elif subject == "genre":
                for genre in GENRES:
                    if result in GENRES[genre]:
                        found = genre

            identifiers.append(found)

        if len(identifiers) == 0:
            return []
        else:
            if len(identifiers) <= 3:
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

            if rating >= 7.0:
                return "very_positive"
            elif rating >= 6.0:
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
            "Western": "positive",
        }
        if genre == "Genre":
            if not (attitude is None):
                res = []
                for k in genres:
                    if genres[k] == attitude:
                        res += [k]
                return res
            else:
                return []
        else:
            return genres[genre]

    def get_movie_names(self, imdb_id):
        names = []
        if "title" in self.database[imdb_id]:
            names.append(self.database[imdb_id]["title"])
        if "original_title" in self.database[imdb_id]:
            if self.database[imdb_id]["original_title"] not in names:
                names.append(self.database[imdb_id]["original_title"])
        if "all_titles" in self.database[imdb_id]:
            for n in self.database[imdb_id]["all_titles"]:
                if n not in names:
                    names.append(n)
        return names
