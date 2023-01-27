import re
import logging
from common.universal_templates import if_chat_about_particular_topic
from common.utils import get_topics, TOPIC_GROUPS

logger = logging.getLogger(__name__)

TOP_5k_FREQUENT_WORDS = set(
    [k.strip() for k in open("common/google-10000-english-no-swears.txt", "r").readlines()[:5000]]
)

GOSSIP_COMPILED_PATTERN = re.compile(
    r"\b(celebrit|actor|actress|writer|author|entrepreneur|sportsperson|musician|gossip)", re.IGNORECASE
)
HAVE_YOU_GOSSIP_TEMPLATE = re.compile(r"(would|have|did|was|had|were|are|do) you .*gossip", re.IGNORECASE)

GOSSIP_SKILL_TRIGGER_PHRASES = [
    "Would you want to hear the latest gossip?",
    "Are you interested in the latest gossip?",
    "Would you be interested in the latest gossip?",
]

CELEBRITY_TRIGGER_PHRASES = ["What is your favourite celebrity?"]

TOPICS_TO_PEOPLE_MAPPINGS = [
    {
        "Topic": "Entertainment_Movies",
        "People": [
            "Christian Bale",
            "Jake Gyllenhaal",
            "Leonardo DiCaprio",
            "Tom Hardy",
            "Joaquin Phoenix",
            "Hugh Jackman",
            "Brad Pitt",
            "Ryan Gosling",
            "Tom Cruise",
            "Bradley Cooper",
            "Amy Adams",
            "Scarlett Johansson",
            "Emma Stone",
            "Anne Hathaway",
            "Emily Blunt",
            "Margot Robbie",
            "Jennifer Lawrence",
            "Rachel McAdams",
            "Saoirse Ronan",
            "Amanda Seyfried",
        ],
    },
    {
        "Topic": "Entertainment_Music",
        "People": [
            "Ed Sheeran",
            "Justin Bieber",
            "Katy Perry",
            "Maroon 5",
            "Post Malone",
            "Lady Gaga",
            "Ariana Grande",
            "Imagine Dragons",
            "The Weeknd",
            "Nicki Minaj",
            "Eminem",
            "Luke Bryan",
            "P!nk",
            "One Direction",
            "Justin Timberlake",
            "Kendrick Lamar",
            "Lady A",
            "Beyonce",
            "Jason Aldean",
            "Sam Smith",
        ],
    },
    {
        "Topic": "Entertainment_Books",
        "People": [
            "Colson Whitehead",
            "Madeline Miller",
            "Yaa Gyasi",
            "Lauren Groff",
            "George Saunders",
            "Karen Russell",
            "Jemisin",
            "Lisa Ko",
            "Emily St. John Mandel",
            "Jesmyn Ward",
            "Brandon Sanderson",
            "John Darnielle",
            "Celeste Ng",
            "Ta-Nehisi Coates",
            "Donna Tartt",
            "Erin Morgenstern",
            "Akhil Sharma",
            "Zadie Smith",
            "Patrick Rothfuss",
            "Kate Atkinson",
        ],
    },
    {
        "Topic": "Entertainment_General",
        "People": [
            "Jennifer Lawrence",
            "Chris Pratt",
            "Brie Larson",
            "Benedict Cumberbatch",
            "Phoebe Waller-Bridge",
            "Oscar Isaac",
            "Emma Stone",
            "Adam Driver",
            "Sophie Turner",
            "Donald Glover",
            "Melissa McCarthy",
            "Eddie Redmayne",
            "Amy Schumer",
            "Rami Malek",
            "Margot Robbie",
            "Andrew Garfield",
            "Karen Gillan",
            "Chris Hemsworth",
            "Millie Bobbie Brown",
            "Finn Wolfhard",
        ],
    },
    {
        "Topic": "Sports",
        "People": [
            "LeBron James",
            "Serena Williams",
            "Tom Brady",
            "Simone Biles",
            "Usain Bolt",
            "Mike Trout",
            "Steph Curry",
            "Lionel Messi",
            "Michael Phelps",
            "Novak Djokovic",
            "Katie Ledecky",
            "Kevin Durant",
            "Rafel Nadal",
            "Cristiano Ronaldo",
            "Aaron Rodgers",
            "Roger Federer",
            "Sidney Crosby",
            "Clayton Kershaw",
            "Alex Ovechkin",
            "Carli Lloyd",
        ],
    },
    {
        "Topic": "Politics",
        "People": [
            # "Donald Trump",
            # "Barack Obama",
            # "Hillary Clinton",
            # "Brett Kavanaugh",
            # "Nancy Pelosi",
            # "Ted Cruz",
            # "Marco Rubio",
            # "Beto O'Rourke",
            # "Alexandria Ocasio-Cortez",
            # "Arnold Schwarzenegger",
            # "Joe Biden"
        ],
    },
    {
        "Topic": "Science_and_Technology",
        "People": [
            "Elon Musk",
            "Jeff Bezos",
            "Bill Gates",
            "Tim Timberlake",
            # "Philip Scheinfeld",
            # "Jayson Waller",
            # "Alfredo Delgado",
            # "Katie Hamilton",
            # "Billionaire Barbie",
            # "Alan Belcher",
            # "Los Silva",
            # "Van Taylor",
            # "David Granados",
            # "Randall Emmett",
            # "Rob Deutsch",
            # "Adam Weitsman",
            # "David Meltzer",
            # "Brady Bell",
            # "Andrew Andrawes",
            # "Jordan Montgomery",
            # "Eric Marcus",
            # "Ben Newman",
            # "Tai Lopez",
            # "Grant Cardone",
            # "Rudy Mawer",
            # "Paul Vigario",
            # "Amber Voight",
            # "Cesar Gomez",
        ],
    },
    {"Topic": "Phatic", "People": []},
    {"Topic": "Interactive", "People": []},
    {"Topic": "Inappropriate_Content", "People": []},
    {"Topic": "Other", "People": []},
]


COBOT_TOPICS_TO_WIKI_OCCUPATIONS = {
    "Politics": [["Q82955", "politician"], ["Q193391", "diplomat"]],
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


def skill_trigger_phrases():
    return GOSSIP_SKILL_TRIGGER_PHRASES + CELEBRITY_TRIGGER_PHRASES


def talk_about_gossip(human_utterance, bot_utterance):
    user_lets_chat_about = if_chat_about_particular_topic(
        human_utterance, bot_utterance, compiled_pattern=GOSSIP_COMPILED_PATTERN
    )
    flag = bool(user_lets_chat_about)
    return flag


def get_all_supported_occupations_lists():
    all_occupations = []

    all_topics_mappings = TOPICS_TO_PEOPLE_MAPPINGS
    for topic_mapping in all_topics_mappings:
        topic = topic_mapping["Topic"]
        people = []
        people = topic_mapping["People"]
        if len(people) > 0:
            raw_occupations_list = COBOT_TOPICS_TO_WIKI_OCCUPATIONS[topic]
            for occupation_pair in raw_occupations_list:
                occupation_id = occupation_pair[0]
                all_occupations.append(occupation_id)

    return all_occupations


def celebrity_from_uttr(human_utterance):
    logger.debug(f'Calling get_celebrity_from_uttr on {human_utterance["text"]}')

    # we need to get all supported occupations
    raw_profession_list = get_all_supported_occupations_lists()

    celebrity_name, matching_types, mismatching_types = None, None, None
    entity_dict = human_utterance["annotations"].get("wiki_parser", {}).get("topic_skill_entities_info", {})
    logger.info(f"found entities: {entity_dict}")
    for celebrity_name in entity_dict:
        if (
            "occupation" in entity_dict[celebrity_name]
            and entity_dict[celebrity_name]["pos"] == 0
            and entity_dict[celebrity_name]["conf"] > 0.5
            and celebrity_name.lower() not in TOP_5k_FREQUENT_WORDS
        ):
            occupation_list = entity_dict[celebrity_name]["occupation"]
            matching_types = [job[1] for job in occupation_list if job[0] in raw_profession_list]
            mismatching_types = [job[1] for job in occupation_list if job[0] not in raw_profession_list]
            if matching_types:
                break
    if not matching_types:
        return None, None, None
    celebrity_name = celebrity_name.title()
    logger.warning(f"Relations {celebrity_name} {matching_types} {mismatching_types}")
    return celebrity_name, matching_types, mismatching_types


def check_is_celebrity_mentioned(human_utterance):
    celebrity_name, _, _ = celebrity_from_uttr(human_utterance)
    if celebrity_name is not None:
        return True
    return False


def about_celebrities(annotated_utterance):
    found_topics = get_topics(annotated_utterance, probs=False, which="all")
    if any([topic in found_topics for topic in TOPIC_GROUPS["celebrities"]]):
        return True
    elif re.findall(GOSSIP_COMPILED_PATTERN, annotated_utterance["text"]):
        return True
    else:
        return False
