import json
from collections import defaultdict

COUNTRIES = "data/countries.json"
USA_COUNTIES = "data/usa_counties.json"
USA_STATES = "data/usa_states.json"


class Database:
    def __init__(self):
        self._countries = defaultdict(lambda: 0)  # dict[country, population]
        self._states = defaultdict(lambda: 0)  # USA ONLY # dict[state, population]
        self._counties = defaultdict(lambda: 0)  # USA ONLY # dict[(state, county), population]
        self._cities = defaultdict(lambda: [])  # USA ONLY # dict[(state, county), [cities]]

        with open(COUNTRIES, "r") as f:
            countries = json.loads(f.read())
            for country, population in countries.items():
                self._countries[country.lower()] = population

        with open(USA_STATES, "r") as f:
            states = json.loads(f.read())
            for state, population in states.items():
                self._states[state.lower()] = population

        with open(USA_COUNTIES, "r") as f:
            data = json.loads(f.read())

            for state, counties in data.items():
                for county, meta in counties.items():
                    self._counties[(state.lower(), county.lower())] = meta["population"]
                    self._cities[(state.lower(), county.lower())] = meta["cities"]

    def country(self, country: str) -> int:
        return self._countries[country.lower()]

    def state(self, state: str) -> int:
        return self._states[state.lower()]

    def county(self, state, county) -> int:
        return self._counties[(state.lower(), county.lower())]

    def county_cities(self, state, county) -> list[str]:
        return self._cities[(state.lower(), county.lower())]

    def cities(self) -> list[tuple[str, str, str]]:
        result = []
        for subject, cities in self._cities.items():
            for city in cities:
                result.append((subject[0], subject[1], city))  # tuple[state, county, city]
        return result

    def counties(self) -> list[tuple[str, str]]:
        return [*self._counties.keys()]  # tuple[state, county]

    def states(self) -> list[str]:
        return [*self._states.keys()]

    def countries(self) -> list[str]:
        return [*self._countries.keys()]


database = Database()
