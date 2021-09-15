import string
import re
import json
from collections.abc import Iterable, Sequence
from typing import List

from ahocorapy.keywordtree import KeywordTree


class OWMCitySlot:
    def __init__(self, path_to_geo_entities: str = "data/openweathermap_city_list.json") -> None:
        """Initializes a trie for finding city names

        :param path_to_geo_entities: filepath to a JSON file containing a list of cities
            file format: ["Ḩeşār-e Sefīd", "‘Ayn Ḩalāqīm", "Taglag", ..... , "Gerton"]
            this list was created using the source file: https://bulk.openweathermap.org/sample/city.list.json.gz
        """
        self.geonames = self._load_from_json(path_to_geo_entities)
        self.kwtree = KeywordTree(case_insensitive=True)
        for geo in self.geonames:
            self.kwtree.add(f" {geo} ")
        self.kwtree.finalize()

    def _load_from_json(self, path_to_geo_entities: str) -> List[str]:
        with open(path_to_geo_entities, "r", encoding="utf-8") as f:
            json_data = json.load(f)
        geonames = set()
        for city in json_data:
            geonames.add(city)
        return list(geonames)

    def find_geo_names_in_utterance(self, utterance: str) -> str:
        """
        Interface method for searching the first occurence of the geo name in utterance
        :param utterance: str with user utterance
        :return: None if nothing found, str with name of geo if something found.
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

    def get_best_match(self, results: Iterable[Sequence[str, int]]) -> str:
        """
         we need to select the entity which is longest and start the earliest
         (usually earliest entity is the most precise)
         for example for the utterance: "west valley city utah", we receive:
         [(' West ', 0), (' West Valley ', 0), (' Valley ', 5), (' West Valley City ', 0),
         (' Valley City ', 5), (' Utah ', 17)]
         we should select "West Valley City".
        :param results:
        :type results:
        :return:
        :rtype:
        """

        best_match = ""
        if results:
            results = sorted(results, key=lambda entity: (entity[1], -len(entity[0].strip())))
            best_match = results[0][0].strip()
        return best_match

    def __call__(self, *args, **kwargs) -> str:
        return self.find_geo_names_in_utterance(*args, **kwargs)
