import json
import re
import string
from collections.abc import Iterable
from typing import List, Tuple

from ahocorapy.keywordtree import KeywordTree


class OWMCitySlot:
    def __init__(self, path_to_geo_entities: str = "data/openweathermap_city_list.json") -> None:
        """Initialize a trie for finding city names.

        :param path_to_geo_entities: filepath to a JSON file containing a list of cities
            file format: ["Ḩeşār-e Sefīd", "‘Ayn Ḩalāqīm", "Taglag", ..... , "Gerton"]
            this list was created using the source file: https://bulk.openweathermap.org/sample/city.list.json.gz
        :type path_to_geo_entities: str
        """
        self.geonames = self._load_from_json(path_to_geo_entities)
        self.kwtree = KeywordTree(case_insensitive=True)
        for geo in self.geonames:
            self.kwtree.add(f" {geo} ")
        self.kwtree.finalize()

    def _load_from_json(self, path_to_geo_entities: str) -> List[str]:
        """Load a list with city names from a JSON file.

        :param path_to_geo_entities: filepath to a JSON file
        :type path_to_geo_entities: str
        :return: a list containing city names
        :rtype: List[str]
        """
        with open(path_to_geo_entities, "r", encoding="utf-8") as f:
            json_data = json.load(f)
        geonames = set()
        for city in json_data:
            geonames.add(city)
        return list(geonames)

    def find_geo_names_in_utterance(self, utterance: str) -> str:
        """Search the first occurrence of the location name in utterance.

        :param utterance: human utterance
        :type utterance: str
        :return: a location name or an empty string if nothing found
        :rtype: str
        """
        # replace punctuation with spaces
        for p in string.punctuation:
            utterance = utterance.replace(p, " ")
        # delete excessive spaces
        utterance = re.sub(r"\s{2,}", " ", utterance.lower()).strip()
        results = list(self.kwtree.search_all(" %s " % utterance))
        # TODO the method could be improved if we search all geo names and then filter
        # the most precises geo entity.
        # User may write: "Massachusetts Boston" -> It has 2 entities, and Boston is preferred
        # because it is more precise location.
        return self.get_best_match(results)

    def get_best_match(self, results: Iterable[Tuple[str, int]]) -> str:
        """Select from the objects with the lowest index the object with the longest length.

         Usually the earliest entity is the most precise.
         For example for the utterance: "west valley city utah", we receive:
         [(' West ', 0), (' West Valley ', 0), (' Valley ', 5), (' West Valley City ', 0),
         (' Valley City ', 5), (' Utah ', 17)], we should select "West Valley City".

        :param results: a sequence with the following pairs (<location_name>, <index>)
        :type results: Iterable[Sequence[str, int]]
        :return: the best match or an empty string if the results are empty
        :rtype: str
        """
        best_match = ""
        if results:
            results = sorted(results, key=lambda entity: (entity[1], -len(entity[0].strip())))
            best_match = results[0][0].strip()
        return best_match

    def __call__(self, *args, **kwargs) -> str:
        """Find the best match in the trie.

        :return: a location name or an empty string if nothing found
        :rtype: str
        """
        return self.find_geo_names_in_utterance(*args, **kwargs)
