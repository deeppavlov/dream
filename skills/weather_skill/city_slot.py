import string
import re
import json
from ahocorapy.keywordtree import KeywordTree


class OWMCitySlot:
    def __init__(self, path_to_geo_entities="/data/openweathermap_city.list.json"):

        self.geonames = self._load_from_json(path_to_geo_entities)

        self.kwtree = KeywordTree(case_insensitive=True)
        for geo in self.geonames:
            self.kwtree.add(f" {geo} ")

        self.kwtree.finalize()

    def _load_from_json(self, path_to_geo_entities):
        with open(path_to_geo_entities, "r") as fi:
            json_data = json.load(fi)
        geonames = [city_dict["name"] for city_dict in json_data]
        geonames_deduplicated = list(set(geonames))
        return geonames_deduplicated

    def find_geo_names_in_utterance(self, utterance):
        """
        Interface method for searching the first occurence of the geo name in utterance
        :param utterance: str with user utterance
        :return: None if nothing found, str with name of geo if something found.
        """
        # preprocess utterance by:
        # replace punct with spaces
        # strip excessive spaces
        puncts = string.punctuation
        for p in puncts:
            utterance = utterance.replace(p, " ")
        utterance = re.sub(r"\s\s+", " ", utterance.lower()).strip()
        results = list(self.kwtree.search_all(" %s " % utterance))
        # TODO the method could be improved if we search all geo names and then filter
        # the most precises geo entity.
        # User may write: "Massachusetts Boston" -> It has 2 entities, and Boston is preferred
        # because it is more precise location.
        if results:
            # found name!
            return self.get_best_match(results)
        else:
            # no geos
            return

    def get_best_match(self, results):
        """
         we need to select the entity which is longest and start the earliest
         (usually earliest entity is the most precise)
         for example for the utterance: "west valley city utah", we receive:
         [(' West ', 0), (' West Valley ', 0), (' Valley ', 5), (' West Valley City ', 0),
         (' Valley City ', 5), (' Utah ', 17)]
         we should select "West Valley City".
        :param results:
        :return:
        """

        earliest_index = None
        geo_candidate = None

        for each_geo, each_start_index in results:
            each_geo = each_geo.strip()
            if earliest_index is None:
                earliest_index = each_start_index
                geo_candidate = each_geo

            if each_start_index > earliest_index:
                continue

            if each_start_index < earliest_index:
                earliest_index = each_start_index
                geo_candidate = each_geo

            if len(each_geo) > len(geo_candidate):
                geo_candidate = each_geo
        return geo_candidate

    def __call__(self, *args, **kwargs):
        return self.find_geo_names_in_utterance(*args, **kwargs)
