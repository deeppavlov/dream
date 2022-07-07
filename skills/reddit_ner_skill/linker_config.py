#!/usr/bin/env python

from itertools import chain

# Entity classes to be cached

entity_classes = {
    "aio:HumanBeing": [
        "aio:Model",
        "aio:Celebrity",
        "aio:Actor",
        "aio:FilmDirector",
        "aio:FilmProducer",
        "aio:Musician",
        "aio:VicePresident",
        "aio:President",
        "aio:UsPresidentialCandidate" "aio:Politician",
        "aio:Diplomat",
        "aio:UsRepublican",
        "aio:UsDemocrat",
        "aio:UsCongressperson",
        "aio:HeadOfGovernment",
        "aio:Businessperson",
        "aio:Athlete",
        "aio:OlympicAthlete",
        "aio:Soldier",
        "aio:Journalist",
        "aio:Comedian",
        "aio:TvPersonality",
        "aio:MemberOfRoyalty",
        "aio:Director",
        "aio:Writer",
        "aio:Inventor",
        "aio:Scientist",
        "aio:Academic",
        "aio:Engineer",
    ],
    "aio:Organisation": [
        "aio:Business",
        "aie:corporation",
        "aie:institution",
        "aio:SportsTeam",
        "aio:PoliticalParty",
        "aio:Government",
        "aio:GovernmentalOrganisation",
    ],
    "aio:GeographicalArea": [
        "aio:WorldHeritageSite",
        "aio:SportsTeamLocation",
        "aio:OfficialResidence",
        "aio:Settlement",
        "aio:State",
        "aio:Country",
        "aie:city",
        "aio:AreaWithinANation",
        "aio:PopulatedPlace",
    ],
    "aio:Thing": [
        "aio:UsPresidentialElection",
        "aio:OlympicGames",
        "aio:Disease",
        "aio:Ensemble",
        "aio:Album",
        "aio:FilmGenre",
        "aio:MusicGenre"
        #         "aio:WrittenPublication",
        #         "aio:MusicPublication",
        "aio:Book",
        "aio:AudioWork",
        "aio:Song",
        "aio:Movie",
        "aio:TvSeries",
        "aie:language",
    ],
}

# Type of connections
# If two entities satisfy the constrains and the condition run by query, then the connection is established
# answer = {'entities':`query_result`, 'status':`query_status`}

human_to_human = [
    {
        "name": "bothStarredIn",
        "constrains": {"a": [("class", "aio:Actor")], "b": [("class", "aio:Actor")]},
        "query": "query m | a <aio:isAStarIn> m | b <aio:isAStarIn> m",
        "condition": lambda answer: len(set(answer["entities"]).intersection(entity_classes)) > 0,
        "bidirectional": True,
    },
    {
        "name": "ActedInAFilmDirectedBy",
        "constrains": {"a": [("class", "aio:Actor")], "b": [("class", "aio:FilmDirector")]},
        "query": "query m | a <aio:isAStarIn> m | b <aio:directed> m",
        "condition": lambda answer: len(set(answer["entities"]).intersection(entity_classes)) > 0,
        "bidirectional": False,
    },
    {
        "name": "DirectedMovieWith",
        "constrains": {"a": [("class", "aio:FilmDirector")], "b": [("class", "aio:Actor")]},
        "query": "query m | a <aio:directed> m | b <aio:isAStarIn> m",
        "condition": lambda answer: len(set(answer["entities"]).intersection(entity_classes)) > 0,
        "bidirectional": False,
    },
    {
        "name": "InSamePoliticalParty",
        "constrains": {"a": [("class", "aio:Politician")], "b": [("class", "aio:Politician")]},
        "query": "query m | a <aio:isAMemberOf> m | b <aio:isAMemberOf> m",
        "condition": lambda answer: len(set(answer["entities"]).intersection(entity_classes)) > 0,
        "bidirectional": False,
    },
    {
        "name": "PresidentAndVicePresident",
        "constrains": {"a": [("class", "aio:President")], "b": [("class", "aio:VicePresident")]},
        "query": "query m | a <aio:isThePresidentOf> m | b <aio:isTheVicePresidentOf> m",
        "condition": lambda answer: len(set(answer["entities"]).intersection(entity_classes)) > 0,
        "bidirectional": True,
    },
    {
        "name": "bothActors",  # Same entity class connections
        "constrains": {"a": [("class", "aio:Actor")], "b": [("class", "aio:Actor")]},
        "query": "",
        "condition": lambda answer: True,
        "bidirectional": True,
    },
    {
        "name": "bothPoliticians",
        "constrains": {"a": [("class", "aio:Politician")], "b": [("class", "aio:Politician")]},
        "query": "",
        "condition": lambda answer: True,
        "bidirectional": True,
    },
    {
        "name": "bothMusicians",
        "constrains": {"a": [("class", "aio:Musician")], "b": [("class", "aio:Musician")]},
        "query": "",
        "condition": lambda answer: True,
        "bidirectional": True,
    },
    {
        "name": "bothFilmDirectors",
        "constrains": {"a": [("class", "aio:FilmDirector")], "b": [("class", "aio:FilmDirector")]},
        "query": "",
        "condition": lambda answer: True,
        "bidirectional": True,
    },
    {
        "name": "bothAthletes",
        "constrains": {"a": [("class", "aio:Athlete")], "b": [("class", "aio:Athlete")]},
        "query": "",
        "condition": lambda answer: True,
        "bidirectional": True,
    },
    {
        "name": "bothModels",
        "constrains": {"a": [("class", "aio:Model")], "b": [("class", "aio:Model")]},
        "query": "",
        "condition": lambda answer: True,
        "bidirectional": True,
    },
    {
        "name": "bothPresidents",
        "constrains": {"a": [("class", "aio:President")], "b": [("class", "aio:President")]},
        "query": "",
        "condition": lambda answer: True,
        "bidirectional": True,
    },
    {
        "name": "bothUsPresidentialCandidate",
        "constrains": {
            "a": [("class", "aio:UsPresidentialCandidate")],
            "b": [("class", "aio:UsPresidentialCandidate")],
        },
        "query": "",
        "condition": lambda answer: True,
        "bidirectional": True,
    },
    {
        "name": "bothRepublicans",
        "constrains": {"a": [("class", "aio:UsRepublican")], "b": [("class", "aio:UsRepublican")]},
        "query": "",
        "condition": lambda answer: True,
        "bidirectional": True,
    },
    {
        "name": "bothDemocrats",
        "constrains": {"a": [("class", "aio:UsDemocrat")], "b": [("class", "aio:UsDemocrat")]},
        "query": "",
        "condition": lambda answer: True,
        "bidirectional": True,
    },
    {
        "name": "bothComedians",
        "constrains": {"a": [("class", "aio:Comedian")], "b": [("class", "aio:Comedian")]},
        "query": "",
        "condition": lambda answer: True,
        "bidirectional": True,
    },
    {
        "name": "bothTvPersonalities",
        "constrains": {"a": [("class", "aio:TvPersonality")], "b": [("class", "aio:TvPersonality")]},
        "query": "",
        "condition": lambda answer: True,
        "bidirectional": True,
    },
    {
        "name": "bothMembersOfRoyalty",
        "constrains": {"a": [("class", "aio:MemberOfRoyalty")], "b": [("class", "aio:MemberOfRoyalty")]},
        "query": "",
        "condition": lambda answer: True,
        "bidirectional": True,
    },
    {
        "name": "bothDirectors",
        "constrains": {"a": [("class", "aio:Director")], "b": [("class", "aio:Director")]},
        "query": "",
        "condition": lambda answer: True,
        "bidirectional": True,
    },
    {
        "name": "bothWriters",
        "constrains": {"a": [("class", "aio:Writer")], "b": [("class", "aio:Writer")]},
        "query": "",
        "condition": lambda answer: True,
        "bidirectional": True,
    },
    {
        "name": "bothInventors",
        "constrains": {"a": [("class", "aio:Inventor")], "b": [("class", "aio:Inventor")]},
        "query": "",
        "condition": lambda answer: True,
        "bidirectional": True,
    },
    {
        "name": "bothScientists",
        "constrains": {"a": [("class", "aio:Scientist")], "b": [("class", "aio:Scientist")]},
        "query": "",
        "condition": lambda answer: True,
        "bidirectional": True,
    },
]

human_to_geo = [
    {
        "name": "isLivingIn",
        "constrains": {"a": [("class", "aio:HumanBeing")], "b": [("class", "aio:Country")]},
        "query": "query | a <aio:isLivingIn> b",
        "condition": lambda answer: answer["status"],
        "bidirectional": False,
    },
    {
        "name": "isTheVicePresidentOfTheCountry",
        "constrains": {"a": [("class", "aio:VicePresident")], "b": [("class", "aio:Country")]},
        "query": "query | a <aio:isTheVicePresidentOfTheCountry> b",
        "condition": lambda answer: answer["status"],
        "bidirectional": False,
    },
    {
        "name": "isThePresidentOfTheCountry",
        "constrains": {"a": [("class", "aio:President")], "b": [("class", "aio:Country")]},
        "query": "query | a <aio:isTheVicePresidentOfTheCountry> b",
        "condition": lambda answer: answer["status"],
        "bidirectional": False,
    },
]

human_to_org = [
    {
        "name": "isAMemberOf",
        "constrains": {"a": [("class", "aio:HumanBeing")], "b": [("class", "aio:Organisation")]},
        "query": "query | a <aio:isAMemberOf> b",
        "condition": lambda answer: answer["status"],
        "bidirectional": False,
    },
    {
        "name": "isAFounderOf",
        "constrains": {"a": [("class", "aio:HumanBeing")], "b": [("class", "aio:Organisation")]},
        "query": "query | a <aio:isAFounderOf> b",
        "condition": lambda answer: answer["status"],
        "bidirectional": False,
    },
    {
        "name": "isTheCeoOf",
        "constrains": {"a": [("class", "aio:Director")], "b": [("class", "aio:Business")]},
        "query": "query | a <aio:isTheCeoOf> b",
        "condition": lambda answer: answer["status"],
        "bidirectional": False,
    },
    {
        "name": "isTheCfoOf",
        "constrains": {"a": [("class", "aio:Director")], "b": [("class", "aio:Business")]},
        "query": "query | a <aio:isTheCfoOf> b",
        "condition": lambda answer: answer["status"],
        "bidirectional": False,
    },
]

human_to_thing = [
    {
        "name": "isACandidateInTheElection",
        "constrains": {"a": [("class", "aio:Politician")], "b": [("class", "aio:UsPresidentialElection")]},
        "query": "query | a <aio:isACandidateInTheElection> b",
        "condition": lambda answer: answer["status"],
        "bidirectional": False,
    },
    {
        "name": "DirectedMovie",
        "constrains": {"a": [("class", "aio:FilmDirector")], "b": [("class", "aio:Movie")]},
        "query": "query | a <aio:directed> b",
        "condition": lambda answer: answer["status"],
        "bidirectional": False,
    },
    {
        "name": "wroteTheLyricsTo",
        "constrains": {"a": [("class", "aio:Musician")], "b": [("class", "aio:Song")]},
        "query": "query | a <aio:wroteTheLyricsTo> b",
        "condition": lambda answer: answer["status"],
        "bidirectional": False,
    },
    {
        "name": "WroteBook",
        "constrains": {"a": [("class", "aio:Writter")], "b": [("class", "aio:Book")]},
        "query": "query | b <aio:isABookBy> a",
        "condition": lambda answer: answer["status"],
        "bidirectional": False,
    },
]

geo_to_geo = [
    {
        "name": "isTheCapitalOf",
        "constrains": {"a": [("class", "aie:city")], "b": [("class", "aio:Country")]},
        "query": "query | a <aio:isTheCapitalOf> b",
        "condition": lambda answer: answer["status"],
        "bidirectional": False,
    },
    {
        "name": "isATownIn",
        "constrains": {"a": [("class", "aie:city")], "b": [("class", "aio:Country")]},
        "query": "query | a <aio:isATownIn> b",
        "condition": lambda answer: answer["status"],
        "bidirectional": False,
    },
    {
        "name": "isGeographicallyLocatedWithinOrIsEqualTo",
        "constrains": {"a": [("class", "aie:city")], "b": [("class", "aio:Country")]},
        "query": "query | a <aio:isGeographicallyLocatedWithinOrIsEqualTo> b",
        "condition": lambda answer: answer["status"],
        "bidirectional": False,
    },
]

geo_to_human = [
    {
        "name": "aio:isTheBirthplaceOf",
        "constrains": {"a": [("class", "aie:Country")], "b": [("class", "aio:HumanBeing")]},
        "query": "query | a <aio:isTheBirthplaceOf> b",
        "condition": lambda answer: answer["status"],
        "bidirectional": False,
    },
]
geo_to_org = []
geo_to_thing = []
org_to_org = [
    {
        "name": "bothWebsites",
        "constrains": {"a": [("class", "aio:Business")], "b": [("class", "aio:Business")]},
        "query": "query | a <aio:isAnInstanceOf> <aie:website> | b <aio:isAnInstanceOf> <aie:website>",
        "condition": lambda answer: answer["status"],
        "bidirectional": True,
    },
]
org_to_human = [
    {
        "name": "hasAMemberOf",
        "constrains": {"a": [("class", "aio:Organisation")], "b": [("class", "aio:HumanBeing")]},
        "query": "query | b <aio:isAMemberOf> a",
        "condition": lambda answer: answer["status"],
        "bidirectional": False,
    },
    {
        "name": "wasFoundedBy",
        "constrains": {"a": [("class", "aio:Organisation")], "b": [("class", "aio:HumanBeing")]},
        "query": "query | b <aio:isAFounderOf> a",
        "condition": lambda answer: answer["status"],
        "bidirectional": False,
    },
    {
        "name": "hasACeoOf",
        "constrains": {"a": [("class", "aio:Organisation")], "b": [("class", "aio:HumanBeing")]},
        "query": "query | b <aio:isACeoOF> a",
        "condition": lambda answer: answer["status"],
        "bidirectional": False,
    },
]
org_to_geo = [
    {
        "name": "isBasedIn",
        "constrains": {"a": [("class", "aio:Organisation")], "b": [("class", "aio:GeograpicalArea")]},
        "query": "query | a <aio:isBasedIn> b",
        "condition": lambda answer: answer["status"],
        "bidirectional": False,
    },
    {
        "name": "isAPoliticalPartyIn",
        "constrains": {"a": [("class", "aio:PoliticalParty")], "b": [("class", "aio:GeograpicalArea")]},
        "query": "query | a <aio:isAPoliticalPartyIn> b",
        "condition": lambda answer: answer["status"],
        "bidirectional": False,
    },
    {
        "name": "wasFoundedIn",
        "constrains": {"a": [("class", "aio:Organisation")], "b": [("class", "aio:GeograpicalArea")]},
        "query": "query | a <aio:wasFoundedIn> b",
        "condition": lambda answer: answer["status"],
        "bidirectional": False,
    },
    {
        "name": "hasABranchIn",
        "constrains": {"a": [("class", "aio:Organisation")], "b": [("class", "aio:GeograpicalArea")]},
        "query": "query | a <aio:hasABranchIn> b",
        "condition": lambda answer: answer["status"],
        "bidirectional": False,
    },
]
org_to_thing = []
thing_to_thing = [
    {
        "name": "bothMovies",
        "constrains": {"a": [("class", "aio:Movie")], "b": [("class", "aio:Movie")]},
        "query": "",
        "condition": lambda answer: True,
        "bidirectional": True,
    },
    {
        "name": "BothTvSeries",
        "constrains": {"a": [("class", "aio:TvSeries")], "b": [("class", "aio:TvSeries")]},
        "query": "",
        "condition": lambda answer: True,
        "bidirectional": True,
    },
]
thing_to_human = [
    {
        "name": "actedInMovie",
        "constrains": {"a": [("class", "aio:Movie")], "b": [("class", "aio:Actor")]},
        "query": "query | b <aio:actedIn> a",
        "condition": lambda answer: answer["status"],
        "bidirectional": False,
    },
    {
        "name": "actedInTvSeries",
        "constrains": {"a": [("class", "aio:TvSeries")], "b": [("class", "aio:Actor")]},
        "query": "query | b <aio:actedIn> a",
        "condition": lambda answer: answer["status"],
        "bidirectional": False,
    },
]
thing_to_geo = [
    {
        "name": "isAMovieFrom",
        "constrains": {"a": [("class", "aio:Movie")], "b": [("class", "aio:GeograpicalArea")]},
        "query": "query | a <aio:isAMovieFrom> b",
        "condition": lambda answer: answer["status"],
        "bidirectional": False,
    },
    {
        "name": "isAnOfficialLanguageOf",
        "constrains": {"a": [("class", "aio:language")], "b": [("class", "aio:GeograpicalArea")]},
        "query": "query | a <aio:isAnOfficialLanguageOf> b",
        "condition": lambda answer: answer["status"],
        "bidirectional": False,
    },
]
thing_to_org = []

links = list(
    chain(
        [
            human_to_human,
            human_to_geo,
            human_to_org,
            human_to_thing,
            geo_to_geo,
            geo_to_human,
            geo_to_org,
            geo_to_thing,
            org_to_org,
            org_to_human,
            org_to_geo,
            org_to_thing,
            thing_to_thing,
            thing_to_human,
            thing_to_geo,
            thing_to_org,
        ]
    )
)
