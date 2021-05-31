COBOT_TO_HUMAN_READABLE_TOPICS = {
    "Entertainment_Music": "music",
    "Entertainment_Movies": "movies",
    "Entertainment_Books": "books",
    "Entertainment_General": "celebrities",
    "Sports": "sports",
    "Politics": "politics",
    "Science_and_Technology": "science and technology",
}

# FOR TESTING PURPOSES ONLY
TEMPORARY_NEWS_FOR_COBOT_TOPICS = [
    {
        "Topic": "Entertainment_Movies",
        "News": [
            {
                "Person": "Scarlett Johansson",
                "Title": "Disney will release Scarlett Johansson in Black Widow in theaters and streaming in July",
                "Content": "Natasha Romanoff (Scarlett Johansson) is going back to where it all started",
            },
            {
                "Person": "Jake Gyllenhaal",
                "Title": "Jake Gyllenhaal to Play War Hero in Combat Control, "
                         "MGM Nears Deal for Sam Hargrave-Directed Film",
                "Content": "MGM is in negotiations to acquire Combat Control, "
                           "starring Jake Gyllenhaal and directed by Sam Hargrave - Extraction.",
            },
            {
                "Person": "Anne Hathaway",
                "Title": "Anne Hathaway: The view that women can’t be leaders is a myth that can be torn down",
                "Content": "Hollywood actress Anne Hathaway told CNBC "
                           "Friday that a lack of female representation in positions of power "
                           "is something that can be torn down "
                           "at any moment, when we decide to tear it down..",
            },
            {
                "Person": "Joaquin Phoenix",
                "Title": "Everything Joaquin Phoenix Has Been Up To Since 'Joker'",
                "Content": "Joaquin Phoenix has been acting since he was a child, and has appeared in many films.",
            },
        ],
    }
]

# # Science and Technology:
#     ["Q1650915", "researcher"],
#     ["Q1622272", "university teacher"],
#     ["Q201788",	"historian"],
#     ["Q81096", "engineer"],
#     ["Q901", "scientist"],
#     ["Q170790",	"mathematician"],
#     ["Q169470",	"physicist"],


COBOT_TOPICS_TO_WIKI_OCCUPATIONS = {
    "Politics": [
        ["Q82955", "politician"],
        ["Q193391", "diplomat"]
    ],
    "Science_and_Technology": [["Q131524", "entrepreneur"]],
    "Entertainment_Movies": [
        ["Q33999", "actor"],
        ["Q10800557", "film actor"],
        ["Q2526255", "film director"],
        ["Q28389", "screenwriter"],
        ["Q10798782", "television actor"],
        ["Q3282637", "film producer"],
        ["Q2259451", "stage actor"],
        ["Q3455803", "director"],
        ["Q947873", "television presenter"],
        ["Q222344", "cinematographer"],
        ["Q2405480", "voice actor"],
    ],
    "Entertainment_Books": [
        ["Q36180", "writer"],
        ["Q49757", "poet"],
        ["Q6625963", "novelist"],
        ["Q214917", "playwright"],
        ["Q1607826", "editor"],
    ],
    "Entertainment_General": [
        ["Q1028181", "painter"],
        ["Q483501", "artist"],
        ["Q33231", "photographer"],
        ["Q1281618", "sculptor"],
        ["Q644687", "illustrator"],
        ["Q15296811", "drawer"],
        ["Q1930187", "journalist"],
    ],
    "Sports": [
        ["Q2066131", "athlete"],
        ["Q937857", "association football player"],
        ["Q3665646", "basketball player"],
        ["Q10871364", "baseball player"],
        ["Q12299841", "cricketer"],
        ["Q11513337", "athletics competitor"],
        ["Q19204627", "American football player"],
        ["Q11774891", "ice hockey player"],
        ["Q2309784", "sport cyclist"],
        ["Q628099", "association football manager"],
        ["Q13141064", "badminton player"],
        ["Q10873124", "chess player"],
        ["Q14089670", "rugby union player"],
        ["Q11338576", "boxer"],
        ["Q15117302", "volleyball player"],
        ["Q10843402", "swimmer"],
        ["Q12840545", "handball player"],
        ["Q10833314", "tennis player"],
    ],
    "Entertainment_Music": [
        ["Q177220", "singer"],
        ["Q36834", "composer"],
        ["Q639669", "musician"],
        ["Q753110", "songwriter"],
        ["Q486748", "pianist"],
        ["Q488205", "singer-songwriter"],
        ["Q855091", "guitarist"],
        ["Q2865819", "opera singer"],
    ],
}
