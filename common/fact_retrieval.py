import re

topic_types = {
    "animal": ["Q16521", "Q55983715"],
    "breed": ["Q38547", "Q39367", "Q43577"],
    "fruit": ["Q28149961", "Q3314483", "Q27481647"],
    "vegetable": ["Q11004"],
    "berry": ["Q13184"],
    "food": ["Q2095"],
    "athlete": ["Q2066131", "Q18536342"],
    "team": ["Q20639856", "Q847017"],
    "musician": ["Q488205", "Q36834", "Q177220", "Q753110"],
    "band": ["Q215380", "Q105756498"],
    "song": ["Q134556", "Q7366"],
    "album": ["Q482994"],
    "author": ["Q36180", "Q49757", "Q214917", "Q6625963", "Q28389"],
    "book": ["Q571", "Q277759", "Q8261", "Q47461344", "Q7725634", "Q1667921"],
    "game": ["Q7889"],
    "film": [
        "Q11424",
        "Q29168811",
        "Q24869",
        "Q202866",
        "Q5398426",
        "Q15416",
        "Q20937557",
        "Q2431196",
        "Q10301427",
        "Q130232",
        "Q369747",
        "Q52162262",
    ],
}

topic_titles = {
    "animal": ["distribution", "relationship with humans", "behavior", "behaviour", "cultural", "culture"],
    "breed": [
        "temperament",
        "intelligence",
        "personality",
        "habits",
        "popularity",
        "behaviour",
        "behavior",
        "hunt",
        "culture",
        "literature",
        "train",
        "working dog",
        "emerging breed standard",
    ],
    "athlete": ["club career", "international career", "player profile", "records", "personal life"],
    "team": ["support", "stadium", "colors and mascot", "club rivalries", "records"],
    "musician": ["compositional style", "musical style", "vocal style", "music career", "film career", "personal life"],
    "band": [
        "early years",
        "breakthrough success",
        "band split-up",
        "new line-up",
        "successes and struggles",
        "musical style",
        "development",
        "influences",
        "touring years",
    ],
    "author": ["fictional works", "critics by other authors", "life and career"],
    "book": ["composition history", "principal characters", "background", "film"],
    "game": ["game modes", "multiplayer", "customization", "awards", "films", "virtual reality"],
    "film": [
        "plot",
        "production",
        "development",
        "filming locations",
        "filming",
        "music",
        "films",
        "casting",
        "special effects",
        "score",
    ],
}

re_tokenizer = re.compile(r"[\w']+|[^\w ]")


def find_topic_titles(all_titles, cur_topic_titles):
    page_titles = []
    all_titles_lower = {title.lower(): title for title in all_titles}
    found_title = ""
    for title in cur_topic_titles:
        if title in all_titles_lower:
            found_title = all_titles_lower[title]
            page_titles.append([title, found_title])
        else:
            title_tokens = set(re.findall(re_tokenizer, title))
            for page_title in all_titles:
                page_title_tokens = set(re.findall(re_tokenizer, page_title.lower()))
                if title_tokens.intersection(page_title_tokens):
                    page_titles.append([title, page_title])
                    break
    return page_titles


def get_subtopic_fact(annotations, entity_type, subtopic):
    fact = ""
    entities_facts = annotations.get("fact_retrieval", {}).get("topic_facts", [])
    for entity_facts in entities_facts:
        if entity_facts["entity_type"] == entity_type:
            facts = entity_facts["facts"]
            for entity_fact in facts:
                if entity_fact["title"] == subtopic and entity_fact["sentences"]:
                    fact = entity_fact["sentences"][0]
                    return fact
    return fact


def get_all_facts(annotations, entity_type):
    facts = []
    entities_facts = annotations.get("fact_retrieval", {}).get("topic_facts", [])
    for entity_facts in entities_facts:
        if entity_facts["entity_type"] == entity_type:
            facts = entity_facts["facts"]
            break
    return facts
