import itertools
import logging
import random
import re
from common.universal_templates import COMPILE_WHAT_TO_TALK_ABOUT
from common.animals import ANIMALS_FIND_TEMPLATE
from common.universal_templates import if_chat_about_particular_topic
from common.utils import is_no, is_yes
from common.wiki_skill_scenarios import topic_config

logger = logging.getLogger(__name__)

used_types_dict = [
    {"types": ["Q11253473"], "titles": {"history": "", "hardware": "", "software": ""}},  # smart device
    {"entity_substr": ["hiking"], "page_title": "Hiking", "titles": {"equipment": "", "destinations": ""}},
    {
        "types": ["Q15707583", "Q2239243"],  # fictional animal (for example, unicorn)  # mythical creature
        "titles": {
            "mythology": "",
            "heraldry": "",
            "history": "",
            "modern depictions": "",
            "origin": "",
            "popular culture": "Would you like to know about {} in popular culture?",
        },
    },
    {
        "entity_substr": ["ghosts", "spirits"],
        "page_title": "Ghost",
        "titles": {
            "fear of ghosts": "Are you afraid of ghosts?",
            "common attributes": "I can tell you about ghosts, should I?",
            "ghosts and the afterlife": "Some people believe that ghosts are souls of dead people."
            " Would you like more details?",
        },
    },
    {
        "entity_substr": ["medicine"],
        "page_title": "Medicine",
        "titles": {
            "clinical practice": "",
            "branches": "",
            "quality": "",
            "traditinal medicine": "Would you like to know about traditional medicine?",
        },
    },
    {
        "types": ["Q12140"],  # medication
        "titles": {
            "medical use": "",
            "effect": "",
            "overdose": "",
            "symptoms": "Would you like to know about the symptoms of {} usage?",
            "treatment": "",
            "culture": "Would you like to know about {} in culture?",
        },
    },
    {
        "entity_substr": ["cars", "automobiles"],
        "titles": {
            "autonomous car": "Would you like to know about autonomous car?",
            "car sharing": "Would you like to know about car sharing?",
            "mass production": "Would you like to know about cars in mass production?",
            "environmental impact": "",
        },
    },
    {
        "types": ["Q17737"],  # theory (for example, quantum theory)
        "titles": {
            "fundamental concepts": "",
            "application": "",
            "formulation": "",
            "relation": "Would you like to know about the relation of {} to other theories?",
            "examples": "",
        },
    },
    {
        "types": ["Q1587903", "Q11862829"],  # science  # academic discipline
        "titles": {
            "application": "",
            "research methods": "",
            "themes": "Would you like to know about basic themes of {}?",
            "major schools": "",
            "relation": "Would you like to know about the relation of {} to other fields?",
            "research fields": "",
            "core theories": "",
        },
    },
    {
        "types": ["Q334166", "Q752870"],  # transport  # motor vehicle
        "titles": {"uses": "", "usage": "", "repair": "", "technical aspects": "", "parts": "", "design": ""},
    },
    {
        "types": ["Q7278"],  # political party
        "titles": {
            "symbols": "",
            "ideology": "",
            "voter": "Would you like to know about voters of {}",
            "structure": "",
        },
    },
    {
        "entity_substr": ["minecraft"],
        "types": ["Q7889"],  # video game
        "wikihow_info": {"Build-a-Wooden-House-in-Minecraft": ""},
        "titles": {
            "game modes": "",
            "multiplayer": "",
            "customization": "",
            "awards": "",
            "films": "Would you like to know about films based on {}?",
            "virtual reality": "Would you like to know how {} can be played using virtual reality?",
        },
    },
    {"entity_substr": ["tiktok"], "page_title": "TikTok", "titles": {"viral trends": "", "users": "", "features": ""}},
    {
        "entity_substr": ["artificial intelligence"],
        "page_title": "Artificial intelligence",
        "titles": {
            "natural language processing": "Would you like to know about natural language processing?",
            "knowledge representation": "Would you like to hear about knowledge representation in {}?",
            "symbolic": "Are you interested in symbolic {}?",
            "brain simulation": "Would you like to know about brain simulation?",
            "applications": "",
            "risks": "",
        },
    },
    {
        "types": ["Q1114461", "Q95074"],  # comics character, fictional character
        "titles": {
            "personality": "",
            "skills": "",
            "early years": "",
            "conception": "",
            "voice": "",
            "creation": "Would you like to learn how {} was created?",
            "character biography": "",
        },
    },
    {
        "entity_substr": ["politic", "politics"],
        "page_title": "Politics",
        "titles": {
            "forms of government": "Would you like to know about forms of government?",
            "political culture": "Are you interested in political culture?",
            "political corruption": "Do you want to hear about political corruption?",
            "democracy": "Would you like to learn about democracy?",
            "ancient history": "",
            "political conflict": "Do you want to hear about political conflicts?",
        },
    },
    {
        "types": ["Q82955", "Q372436"],  # politician
        "titles": {
            "political career": "",
            "early life": "",
            "family": "",
            "religious views": "",
            "early years": "",
            "business career": "",
            "media career": "",
            "domestic policy": "",
            "foreign policy": "",
            "election": "",
            "presidential campaign": "",
            "political positions": "",
            "reputation": "",
        },
    },
    {
        "entity_substr": ["robots", "robot"],
        "page_title": "Robot",
        "titles": {
            "mobile robot": "Would you like to learn about mobile robots?",
            "service robot": "Would you like to hear about service robots?",
            "military robot": "Do you want to learn about military robots?",
            "factory robot": "Are you interested in factory robots?",
            "literature": "Would you like to know about books about robots?",
            "films": "Are you interested in films about robots?",
        },
    },
    {
        "entity_substr": ["religion"],
        "page_title": "Religion",
        "titles": {
            "judaism": "Would you like to know about judaism?",
            "christianity": "Do you want to learn about christianity?",
            "islam": "Would you like to know about islam?",
            "buddhism": "Would you like to know about buddhism?",
        },
    },
    {
        "entity_substr": ["art", "arts"],
        "page_title": "The arts",
        "titles": {
            "architecture": "Would you like to know about architecture?",
            "drawing": "Would you like to know about drawing?",
            "painting": "Would you like to know about painting?",
            "photography": "Would you like to know about photography?",
            "sculpture": "Would you like to know about sculpture?",
            "dance": "Would you like to know about dance?",
            "theatre": "Would you like to know about theatre?",
        },
    },
    {
        "entity_substr": ["dinosaur", "dinosaurs"],
        "page_title": "Dinosaur",
        "titles": {
            "behavior": "",
            "pre-scientific history": "",
            "early dinosaur research": "Would you like to learn about early research of dinosaurs?",
            "discoveries": "",
            "origins and early evolution": "",
        },
    },
    {
        "entity_substr": ["teleportation"],
        "page_title": "Teleportation",
        "titles": {"fiction": "Would you like to know about teleportation in fiction?", "science": ""},
    },
    {
        "types": ["Q198"],  # war
        "titles": {"causes": "", "tactics": "", "general features": "", "diplomacy": "", "outbreak": "", "battles": ""},
    },
    {
        "entity_substr": ["space", "outer space"],
        "page_title": "Space exploration",
        "titles": {
            "first outer space flights": "",
            "first human outer space flight": "",
            "first astronomical body space explorations": "",
            "first space station": "",
            "first interstellar space flight": "",
            "deep space exploration": "",
            "future of space exploration": "",
        },
    },
    {
        "entity_substr": ["cryptocurrency"],
        "page_title": "Cryptocurrency",
        "titles": {
            "blockchain": "Would you like to know about blockchain?",
            "mining": "",
            "darknet markets": "",
            "exchanges": "",
        },
    },
    {
        "entity_substr": ["bitcoin"],
        "page_title": "Bitcoin",
        "titles": {
            "blockchain": "Would you like to know about blockchain?",
            "mining": "",
            "darknet markets": "",
            "exchanges": "",
            "software implementation": "",
            "transactions": "",
        },
    },
    {
        "entity_substr": ["drawing"],
        "page_title": "Drawing",
        "titles": {"technique": "", "materials": "", "process": ""},
    },
    {
        "entity_substr": ["fishing"],
        "page_title": "Fishing",
        "titles": {"traditional fishing": "", "recreational fishing": "", "techniques": ""},
    },
    {
        "types": ["Q105756498", "Q215380"],  # type of musical group, musical group
        "titles": {
            "early years": "",
            "breakthrough success": "",
            "band split-up": "",
            "new line-up": "",
            "successes and struggles": "",
            "musical style": "",
            "development": "",
            "influences": "",
            "awards and achievements": "",
            "touring years": "",
        },
    },
    {
        "types": ["Q16521", "Q55983715", "Q7377"],  # taxon (species of animal)
        "titles": {
            "distribution": "Would you like to know where {} live?",
            "relationship with humans": "",
            "behavior": "",
            "behaviour": "",
            "social structure": "",
            "cultural": "Would you like to know about {} in popular culture?",
            "culture": "Would you like to know about {} in popular culture?",
        },
    },
    {
        "types": ["Q2066131"],  # athlete
        "titles": {"club career": "", "international career": "", "player profile": "", "personal life": ""},
    },
    {"types": ["Q1028181"], "titles": {"style": "", "technique": "", "career": ""}},  # painter
]

re_tokenizer = re.compile(r"[\w']+|[^\w ]")

used_types = set(itertools.chain.from_iterable([elem.get("types", []) for elem in used_types_dict]))
used_substr = set(itertools.chain.from_iterable([elem.get("entity_substr", []) for elem in used_types_dict]))
badlist_words = {"yup", "true", "false", "boy", "boys", "meow", "people", "alexa", "alexa alexa"}
badlist_titles = {"ethymology", "terminology"}

prohibited_topics = {
    "music",
    "films",
    "movies",
    "sport",
    "travel",
    "food",
    "animals",
    "pet",
    "pets",
    "coronavirus",
    "corona virus",
    "gossip",
    "gossips",
    "cat",
    "cats",
    "dog",
    "dogs",
    "pop",
    "rock",
    "rap",
    "video game",
    "video games",
}
prohibited_types = {
    "Q571",  # book
    "Q277759",  # book series
    "Q8261",  # novel
    "Q47461344",  # written work
    "Q7725634",  # literary work
    "Q1667921",  # novel series
    "Q24856",  # film series
    "Q11424",  # film
    "Q29168811",  # animated feature film
    "Q24869",  # feature film
    "Q202866",  # animated film
    "Q31629",  # type of sport
    "Q349",  # sport
    "Q28149961",  # type of fruit
    "Q2095",  # food
}

QUESTION_TEMPLATES = [
    "Would you like to know about {} of {}?",
    "Do you want to learn about {} of {}?",
    "Are you interested in {} of {}?",
    "Do you want to hear about {} of {}?",
    "Do you want to know about {} of {}?",
    "Do you want me to tell you about {} of {}?",
    "The next topic is {} of {}, continue?",
    "Let me tell you about {} of {}, okey?",
]

QUESTION_TEMPLATES_SHORT = [
    "Would you like to know about {}?",
    "Do you want to learn about {}?",
    "Are you interested in {}?",
    "Do you want to hear about {}?",
    "Do you want to know about {}?",
    "Do you want me to tell you about {}?",
    "The next topic is {}, continue?",
    "Let me tell you about {}, okey?",
]

NEWS_MORE = [
    "Do you want more details?",
    "Should I continue?",
    "What is your opinion?",
    "Do you want to hear more?",
    "I can tell you more, okay?",
    "Would you like to learn more?",
]
dff_wiki_phrases = ["Are you listening to music or playing games"]

CONF_DICT = {
    "UNDEFINED": 0.0,
    "USER_QUESTION_IN_BEGIN": 0.8,
    "ENTITY_IN_HISTORY": 0.9,
    "WIKI_TYPE_DOUBT": 0.9,
    "OTHER_DFF_SKILLS": 0.9,
    "WIKI_TYPE": 0.94,
    "IN_SCENARIO": 0.95,
    "SURE_WIKI_TYPE": 0.98,
    "WIKI_TOPIC": 0.99,
    "HIGH_CONF": 1.0,
}
WIKI_BADLIST = re.compile(r"(margin|\bfont\b|wikimedia|wikitable| url )", re.IGNORECASE)

transfer_from_skills = {
    "dff_animals_skill": {
        "Q16521",  # taxon
        "Q55983715",  # organisms known by a particular common name
        "Q38547",  # dog crossbreed
        "Q39367",  # dog breed
        "Q43577",  # cat breed
    },
    "dff_food_skill": {"Q28149961", "Q2095", "Q11004"},
    "dff_sport_skill": {
        "Q2066131",  # athlete
        "Q18536342",  # competitive player
        "Q20639856",  # team
        "Q847017",  # sports club
    },
    "dff_music_skill": {
        "Q488205",  # singer-songwriter
        "Q36834",  # composer
        "Q177220",  # singer
        "Q753110",  # songwriter
        "Q134556",  # single
        "Q7366",  # song
        "Q482994",  # album
    },
    "dff_movie_skill": {"Q11424", "Q24856", "Q10800557", "Q10798782", "Q2405480", "Q5398426", "Q15416", "Q2526255"},
    "dff_book_skill": {
        "Q36180",
        "Q49757",
        "Q214917",
        "Q6625963",
        "Q28389",
        "Q571",
        "Q277759",
        "Q8261",
        "Q47461344",
        "Q7725634",
        "Q1667921",
    },
}


def find_entity_wp(annotations, bot_uttr, specific_types=None):
    conf_type = "UNDEFINED"
    found_entity_substr = ""
    found_entity_id = ""
    found_entity_types = []
    nounphr_label_dict = {}
    nounphrases = annotations.get("cobot_entities", {}).get("labelled_entities", [])
    for nounphr in nounphrases:
        nounphr_text = nounphr.get("text", "")
        nounphr_label = nounphr.get("label", "")
        if nounphr_text and nounphr_label:
            nounphr_label_dict[nounphr_text] = nounphr_label
    bot_text = bot_uttr.get("text", "")
    bot_question = "?" in bot_text
    prev_active_skill = bot_uttr.get("active_skill", "")
    current_types = set()
    if bot_question and prev_active_skill and prev_active_skill in transfer_from_skills:
        current_types = transfer_from_skills[prev_active_skill]
    cobot_topics = annotations.get("cobot_topics", {}).get("text", [])
    wp_output = annotations.get("wiki_parser", {})
    if isinstance(wp_output, dict):
        all_entities_info = wp_output.get("entities_info", {})
        wiki_skill_entities_info = wp_output.get("wiki_skill_entities_info", {})
        topic_skill_entities_info = wp_output.get("topic_skill_entities_info", {})
        for entities_info in [all_entities_info, wiki_skill_entities_info, topic_skill_entities_info]:
            for entity, triplets in entities_info.items():
                entity_id = triplets.get("plain_entity", "")
                types = (
                    triplets.get("types", [])
                    + triplets.get("instance of", [])
                    + triplets.get("subclass of", [])
                    + triplets.get("occupation", [])
                    + triplets.get("types_2hop", [])
                )
                type_ids = [elem for elem, label in types]
                if specific_types:
                    inters = set(type_ids).intersection(specific_types)
                else:
                    inters = set(type_ids).intersection(used_types)
                coherent_with_prev = True
                if current_types and not set(type_ids).intersection(current_types):
                    coherent_with_prev = False
                in_not_used_types = set(type_ids).intersection(prohibited_types)
                in_not_used_topics = entity.lower() in prohibited_topics or entity.lower() in badlist_words
                token_conf = triplets["token_conf"]
                conf = triplets["conf"]
                found_animal = re.findall(ANIMALS_FIND_TEMPLATE, entity)
                in_banned_topics = found_animal or "Food_Drink" in cobot_topics
                if (
                    inters
                    and not in_not_used_topics
                    and not in_banned_topics
                    and nounphr_label_dict.get(entity, "") != "number"
                    and coherent_with_prev
                    and token_conf > 0.5
                    and conf > 0.2
                ):
                    pos = triplets.get("pos", 5)
                    found_entity_substr = entity
                    found_entity_id = entity_id
                    found_entity_types = inters
                    conf_type = "WIKI_TYPE"
                    if token_conf > 0.9 and conf > 0.8 and pos == 0:
                        conf_type = "SURE_WIKI_TYPE"
                    if pos > 0:
                        conf_type = "WIKI_TYPE_DOUBT"
                    if in_not_used_types:
                        conf_type = "OTHER_DFF_SKILLS"
                    break
            if found_entity_substr:
                break

    return found_entity_substr, found_entity_id, found_entity_types, conf_type


def find_entity_types(query_entity, annotations):
    type_ids = set()
    wp_output = annotations.get("wiki_parser", {})
    if isinstance(wp_output, dict):
        all_entities_info = wp_output.get("entities_info", {})
        wiki_skill_entities_info = wp_output.get("wiki_skill_entities_info", {})
        topic_skill_entities_info = wp_output.get("topic_skill_entities_info", {})
        for entities_info in [all_entities_info, wiki_skill_entities_info, topic_skill_entities_info]:
            for entity, triplets in entities_info.items():
                if entity == query_entity:
                    types = (
                        triplets.get("types", [])
                        + triplets.get("instance of", [])
                        + triplets.get("subclass of", [])
                        + triplets.get("occupation", [])
                        + triplets.get("types_2hop", [])
                    )
                    type_ids = set([elem for elem, label in types])
                    return type_ids
    return type_ids


def find_entity_by_types(annotations, types_to_find, relations=None):
    found_entity_wp = ""
    found_types = []
    found_entity_triplets = {}
    wp_output = annotations.get("wiki_parser", {})
    types_to_find = set(types_to_find)
    if isinstance(wp_output, dict):
        all_entities_info = wp_output.get("entities_info", {})
        wiki_skill_entities_info = wp_output.get("wiki_skill_entities_info", {})
        topic_skill_entities_info = wp_output.get("topic_skill_entities_info", {})
        for entities_info in [all_entities_info, wiki_skill_entities_info, topic_skill_entities_info]:
            for entity, triplets in entities_info.items():
                types = (
                    triplets.get("types", [])
                    + triplets.get("instance of", [])
                    + triplets.get("subclass of", [])
                    + triplets.get("types_2_hop", [])
                    + triplets.get("occupation", [])
                )
                type_ids = [elem for elem, label in types]
                logger.info(f"types_to_find {types_to_find} type_ids {type_ids}")
                inters = set(type_ids).intersection(types_to_find)
                conf = triplets["conf"]
                pos = triplets.get("pos", 5)
                if inters and conf > 0.45 and pos < 2:
                    found_entity_wp = entity
                    found_types = list(inters)
                    entity_triplets = {}
                    if relations:
                        for relation in relations:
                            objects_info = triplets.get(relation, [])
                            if objects_info:
                                objects = [obj[1] for obj in objects_info]
                                entity_triplets[relation] = objects
                    if entity_triplets:
                        found_entity_triplets[entity] = entity_triplets
                    break
    return found_entity_wp, found_types, found_entity_triplets


def find_entity_nounphr(annotations):
    found_entity_substr = ""
    conf_type = "UNDEFINED"
    nounphrases = annotations.get("cobot_entities", {}).get("labelled_entities", [])
    found = False
    for nounphr in nounphrases:
        nounphr_text = nounphr.get("text", "")
        nounphr_label = nounphr.get("label", "")
        in_not_used_substr = nounphr_text.lower() in prohibited_topics or nounphr_text.lower() in badlist_words
        if nounphr_text in used_substr and not in_not_used_substr and nounphr_label != "number":
            found_entity_substr = nounphr_text
            conf_type = "WIKI_TOPIC"
            found_animal = re.findall(ANIMALS_FIND_TEMPLATE, found_entity_substr)
            found = True
            if found_animal:
                conf_type = "OTHER_DFF_SKILLS"
            break
        if not found_entity_substr:
            for used_entity_substr in used_substr:
                if (
                    re.findall(rf"\b{nounphr_text}\b", used_entity_substr, re.IGNORECASE)
                    or re.findall(rf"\b{used_entity_substr}\b", nounphr_text, re.IGNORECASE)
                    and not in_not_used_substr
                ):
                    found_entity_substr = used_entity_substr
                    conf_type = "WIKI_TOPIC"
                    found = True
                    break
        if found:
            break

    return found_entity_substr, conf_type


def check_nounphr(annotations, nounphr_to_find):
    nounphrases = annotations.get("cobot_entities", {}).get("labelled_entities", [])
    for nounphr in nounphrases:
        nounphr_text = nounphr.get("text", "")
        nounphr_label = nounphr.get("label", "")
        if nounphr_text in nounphr_to_find and nounphr_label != "number":
            return nounphr_text
    return ""


def find_entity_custom_kg(annotations, kg_type):
    custom_el_info = annotations.get("custom_entity_linking", [])
    for entity_info in custom_el_info:
        substr = entity_info.get("entity_substr", "")
        e_types = entity_info.get("entity_id_tags", [])
        if any([e_type.lower() == kg_type.lower() for e_type in e_types]):
            return substr
    return ""


def find_entity_prex(annotations, prop):
    prop = prop.replace("_", " ")
    prex_info_batch = annotations.get("property_extraction", [])
    for prex_info in prex_info_batch:
        if isinstance(prex_info, list) and prex_info:
            prex_info = prex_info[0]
        if prex_info:
            triplets = prex_info.get("triplets", [])
            for triplet in triplets:
                if "relation" in triplet:
                    rel = triplet["relation"]
                elif "property" in triplet:
                    rel = triplet["property"]
                obj = triplet["object"]
                if rel.replace("_", " ").lower() == prop.replace("_", " ").lower():
                    return obj
    return ""


def extract_entity(ctx, entity_type):
    user_uttr: dict = ctx.misc.get("agent", {}).get("dialog", {}).get("human_utterances", [{}])[-1]
    annotations = user_uttr.get("annotations", {})
    logger.info(f"annotations {annotations}")
    if entity_type.startswith("tags"):
        tag = entity_type.split("tags:")[1]
        nounphrases = annotations.get("entity_detection", {}).get("labelled_entities", [])
        for nounphr in nounphrases:
            nounphr_text = nounphr.get("text", "")
            nounphr_label = nounphr.get("label", "")
            if nounphr_label == tag:
                found_entity = nounphr_text
                return found_entity
    elif entity_type.startswith("wiki"):
        wp_type = entity_type.split("wiki:")[1]
        found_entity, *_ = find_entity_by_types(annotations, [wp_type])
        if found_entity:
            return found_entity
    elif entity_type.startswith("prop:"):
        user_property = entity_type.split("prop:")[1]
        obj = find_entity_prex(annotations, user_property)
        return obj
    elif entity_type.startswith("kg"):
        kg_type = entity_type.split("kg:")[1]
        found_entity = find_entity_custom_kg(annotations, kg_type)
        if found_entity:
            return found_entity
    elif entity_type == "any_entity":
        entities = annotations.get("entity_detection", {}).get("entities", [])
        if entities:
            return entities[0]
    else:
        res = re.findall(entity_type, user_uttr.get("text", ""))
        if res:
            return res[0]
    return ""


def if_user_dont_know_topic(user_uttr, bot_uttr):
    flag = False
    what_to_talk_about = re.findall(COMPILE_WHAT_TO_TALK_ABOUT, bot_uttr.get("text", ""))
    user_dont_know = re.findall("(do not|dont|don't) know", user_uttr["text"]) or re.findall(
        "(anything|everything)", user_uttr["text"]
    )
    if what_to_talk_about and user_dont_know:
        flag = True
    return flag


def check_condition_element(elem, user_uttr, bot_uttr, shared_memory={}):
    flag = False
    annotations = user_uttr["annotations"]
    isyes = is_yes(user_uttr)
    isno = is_no(user_uttr)
    user_info = shared_memory.get("user_info", {})
    entity_triplets = shared_memory.get("entity_triplets", {})
    if elem[0] == "is_yes" and isyes:
        flag = True
    elif elem[0] == "is_no" and isno:
        flag = True
    elif "pattern" in elem[0]:
        pattern = elem[0]["pattern"]
        if elem[1] == "user" and (
            (isinstance(pattern, str) and re.findall(pattern, user_uttr["text"], re.IGNORECASE))
            or (isinstance(pattern, re.Pattern) and re.findall(pattern, user_uttr["text"]))
        ):
            flag = True
        if elem[1] == "bot" and (
            (isinstance(pattern, str) and re.findall(pattern, bot_uttr.get("text", ""), re.IGNORECASE))
            or (isinstance(pattern, re.Pattern) and re.findall(pattern, bot_uttr.get("text", "")))
        ):
            flag = True
    elif "cobot_entities_type" in elem[0]:
        cobot_entities_type = elem[0]["cobot_entities_type"]
        nounphrases = annotations.get("cobot_entities", {}).get("labelled_entities", [])
        for nounphr in nounphrases:
            nounphr_label = nounphr.get("label", "")
            if nounphr_label == cobot_entities_type:
                flag = True
    elif "wiki_parser_types" in elem[0]:
        wp_types = elem[0]["wiki_parser_types"]
        found_entity, *_ = find_entity_by_types(annotations, wp_types)
        if found_entity:
            flag = True
    elif "user_info" in elem[0]:
        info_to_check = elem[0]["user_info"]
        for key, value in info_to_check.items():
            if key in user_info and user_info[key] == value:
                flag = True
                break
    elif "entity_triplets" in elem[0]:
        checked_entity_triplets = elem[0]["entity_triplets"]
        objects = set(checked_entity_triplets[-1])
        mem_objects = entity_triplets
        for key in checked_entity_triplets[:-1]:
            if key in user_info:
                key = user_info[key]
            mem_objects = mem_objects.get(key, {})
        if set(mem_objects).intersection(objects):
            flag = True
    elif elem[0] == "any":
        flag = True
    if len(elem) == 3 and not elem[2]:
        flag = not flag
    return flag


def check_condition(condition, user_uttr, bot_uttr, shared_memory):
    flag = False
    checked_elements = []
    for elem in condition:
        if isinstance(elem[0], str) or isinstance(elem[0], dict):
            flag = check_condition_element(elem, user_uttr, bot_uttr, shared_memory)
        elif isinstance(elem[0], list):
            flag = all([check_condition_element(sub_elem, user_uttr, bot_uttr, shared_memory) for sub_elem in elem])
        checked_elements.append(flag)
    if any(checked_elements):
        flag = True
    return flag


def if_switch_test_skill(user_uttr, bot_uttr):
    flag = False
    if re.findall(r"(\bart\b|drawing|painting|photo)", user_uttr["text"], re.IGNORECASE):
        flag = True
    return flag


def if_switch_wiki_skill(user_uttr, bot_uttr):
    flag = False
    user_uttr_annotations = user_uttr["annotations"]
    found_entity_substr, found_entity_id, found_entity_types, conf_type_wp = find_entity_wp(
        user_uttr_annotations, bot_uttr
    )
    found_entity_substr, conf_type_nounphr = find_entity_nounphr(user_uttr_annotations)
    user_dont_know = if_user_dont_know_topic(user_uttr, bot_uttr)
    asked_name = "what is your name" in bot_uttr.get("text", "").lower()
    asked_news = "news" in user_uttr["text"]
    for topic, topic_info in topic_config.items():
        pattern = topic_info.get("pattern", "")
        if (
            (isinstance(pattern, str) and re.findall(pattern, user_uttr["text"], re.IGNORECASE))
            or (isinstance(pattern, re.Pattern) and re.findall(pattern, user_uttr["text"]))
            or if_chat_about_particular_topic(user_uttr, bot_uttr, compiled_pattern=pattern)
        ):
            flag = True
        switch_on = topic_info.get("switch_on", [])
        for switch_elem in switch_on:
            condition = switch_elem["cond"]
            checked_condition = check_condition(condition, user_uttr, bot_uttr, {})
            if checked_condition:
                flag = True
                break

    if (found_entity_id or found_entity_substr or user_dont_know) and not asked_name and not asked_news:
        flag = True
    all_confs = [(conf_type, CONF_DICT[conf_type]) for conf_type in [conf_type_wp, conf_type_nounphr]]
    all_confs = sorted(all_confs, key=lambda x: x[1], reverse=True)
    wiki_skill_conf_type = all_confs[0][0]
    return flag, wiki_skill_conf_type


def if_must_switch(user_uttr, bot_uttr):
    flag = False
    user_uttr_annotations = user_uttr["annotations"]
    lets_chat = if_chat_about_particular_topic(user_uttr, bot_uttr)
    found_entity_substr_wp, *_, conf_type_wp = find_entity_wp(user_uttr_annotations, bot_uttr)
    found_entity_substr_nphr, conf_type_nphr = find_entity_nounphr(user_uttr_annotations)
    if (
        lets_chat
        and (found_entity_substr_wp or found_entity_substr_nphr)
        and (conf_type_wp == "SURE_WIKI_TYPE" or conf_type_nphr == "WIKI_TOPIC")
    ):
        flag = True
    return flag


def switch_wiki_skill_on_news(user_uttr, bot_uttr):
    user_uttr_annotations = user_uttr["annotations"]
    news = user_uttr_annotations.get("news_api_annotator", [])
    if if_chat_about_particular_topic(user_uttr, bot_uttr) and news:
        nounphrases = user_uttr_annotations.get("cobot_entities", {}).get("labelled_entities", [])
        if nounphrases and news:
            for nounphr in nounphrases:
                for elem in news:
                    if (
                        elem["entity"] == nounphr["text"]
                        and "Q5" in find_entity_types(elem["entity"], user_uttr_annotations)
                        and nounphr["text"] not in badlist_words
                        and nounphr["text"] not in prohibited_topics
                    ):
                        return True
    return False


def if_find_entity_in_history(dialog):
    flag = False
    all_user_uttr = dialog["human_utterances"]
    bot_uttr = dialog["bot_utterances"][-1] if len(dialog["bot_utterances"]) else {}
    utt_num = len(all_user_uttr)
    if utt_num > 1:
        for i in range(utt_num - 2, 0, -1):
            annotations = all_user_uttr[i]["annotations"]
            found_entity_substr, found_entity_id, found_entity_types, _ = find_entity_wp(annotations, bot_uttr)
            found_entity_substr, _ = find_entity_nounphr(annotations)
            if found_entity_id or found_entity_substr:
                flag = True
                break
    return flag


def continue_after_topic_skill(dialog):
    supported_prev_skills = ["dff_animals_skill", "dff_music_skill", "dff_sport_skill"]
    all_user_uttr = dialog["human_utterances"]
    all_bot_uttr = dialog["bot_utterances"]
    all_user_uttr.reverse()
    all_bot_uttr.reverse()
    found_entity_substr, found_entity_id, found_page_title, found_entity_types = "", "", "", []
    conf_type = "UNDEFINED"
    for user_uttr, bot_uttr in zip(all_user_uttr, all_bot_uttr):
        prev_topic_skill = bot_uttr.get("active_skill", "")
        annotations = user_uttr["annotations"]
        el = annotations.get("entity_linking", [])
        specific_types = set()
        if prev_topic_skill in supported_prev_skills:
            specific_types = transfer_from_skills.get(prev_topic_skill, set())
        found_entity_substr, found_entity_id, found_entity_types, conf_type = find_entity_wp(
            annotations, bot_uttr, specific_types
        )
        if found_entity_substr and found_entity_id:
            for entity in el:
                if isinstance(entity, dict) and entity["entity_substr"] == found_entity_substr:
                    entity_ids = entity["entity_ids"]
                    pages_titles = entity["entity_pages_titles"]
                    for entity_id, page_title in zip(entity_ids, pages_titles):
                        if entity_id == found_entity_id:
                            found_page_title = page_title
                            break
            break
    return found_entity_substr, found_entity_id, found_entity_types, found_page_title, conf_type


def if_linked_to_wiki_skill(annotations, skill_name):
    flag = False
    found_entity_substr = ""
    found_entity_id = ""
    found_entity_page = ""
    wp_output = annotations.get("wiki_parser", {})
    if isinstance(wp_output, dict):
        entities_info = wp_output.get("entities_info", {})
        for entity, triplets in entities_info.items():
            types = triplets.get("types", []) + triplets.get("instance of", []) + triplets.get("subclass of", [])
            type_ids = [elem for elem, label in types]
            inters = set(type_ids).intersection(transfer_from_skills[skill_name])
            if inters:
                found_entity_substr = entity
                found_entity_id = triplets.get("plain_entity", "")
                break
    el_output = annotations.get("entity_linking", {})
    for entity in el_output:
        if isinstance(entity, dict) and entity["entity_substr"] == found_entity_substr:
            found_entity_ids = entity["entity_ids"]
            found_pages_titles = entity["entity_pages_titles"]
            for entity_id, entity_page in zip(found_entity_ids, found_pages_titles):
                if entity_id == found_entity_id:
                    found_entity_page = entity_page
                    break
    if found_entity_substr and found_entity_page:
        flag = True
    return flag


def choose_title(vars, all_titles, titles_we_use, prev_title, used_titles, curr_pages=None):
    if curr_pages is None:
        curr_pages = []
    found_title = ""
    found_page_title = ""
    if titles_we_use:
        for _ in range(len(all_titles)):
            found = False
            rand_title = random.choice(titles_we_use)
            if rand_title.lower() not in used_titles:
                for title in all_titles:
                    if (
                        rand_title.lower() == title.lower()
                        and rand_title != prev_title
                        and rand_title.lower() not in badlist_titles
                        and not any([rand_title.lower() in curr_page.lower() for curr_page in curr_pages])
                    ):
                        found_title = rand_title
                        found_page_title = title
                        found = True
                        break
                if not found:
                    for title in all_titles:
                        if (
                            rand_title.lower() in title.lower()
                            and rand_title != prev_title
                            and rand_title.lower() not in badlist_titles
                            and not any([rand_title.lower() in curr_page.lower() for curr_page in curr_pages])
                        ):
                            found_title = rand_title
                            found_page_title = title
                            found = True
                            break
            if found:
                break
    if not found_title:
        titles_we_use = set(all_titles).difference({"first_par"})
        if len(titles_we_use) > len(used_titles):
            for title in titles_we_use:
                if (
                    title.lower() not in used_titles
                    and title.lower() not in badlist_titles
                    and not any([title.lower() in curr_page.lower() for curr_page in curr_pages])
                ):
                    found_title = title.lower()
                    found_page_title = title
    return found_title, found_page_title


def find_page_title(all_titles, title):
    found_page_title = ""
    for page_title in all_titles:
        if page_title.lower() == title.lower():
            found_page_title = page_title
            break
    if not found_page_title:
        title_tokens = set(re.findall(re_tokenizer, title.lower()))
        for page_title in all_titles:
            page_title_tokens = set(re.findall(re_tokenizer, page_title.lower()))
            if title_tokens.intersection(page_title_tokens):
                found_page_title = page_title
                break
    return found_page_title


def find_all_titles(all_titles, topic_facts):
    if isinstance(topic_facts, dict):
        for title in topic_facts:
            all_titles.append(title)
            if isinstance(topic_facts[title], dict):
                all_titles = find_all_titles(all_titles, topic_facts[title])
    return all_titles


def find_par(topic_facts):
    if isinstance(topic_facts, list):
        return topic_facts
    else:
        facts_list = []
        titles = list(topic_facts.keys())
        if "first_par" in titles:
            facts_list += topic_facts["first_par"]
        for title in titles:
            if title != "first_par":
                facts_list += find_par(topic_facts[title])
        return facts_list


def find_paragraph(topic_facts, chosen_title):
    paragraphs = []
    if topic_facts:
        if isinstance(topic_facts, dict):
            for title in topic_facts:
                if title == chosen_title:
                    paragraphs = find_par(topic_facts[title])
                    return paragraphs
                else:
                    paragraphs = find_paragraph(topic_facts[title], chosen_title)
                    if paragraphs:
                        return paragraphs
    return paragraphs


def find_all_paragraphs(topic_facts, paragraphs):
    if topic_facts:
        if isinstance(topic_facts, dict):
            for title in topic_facts:
                paragraphs = find_all_paragraphs(topic_facts[title], paragraphs)
        else:
            paragraphs += topic_facts
    return paragraphs


def delete_hyperlinks(par):
    entities = re.findall(r"\[\[(.*?)]]", par)
    mentions = []
    pages = []
    for entity in entities:
        entity_split = entity.split("|")
        if len(entity_split) == 1:
            replace_str = "[[" + entity_split[0] + "]]"
            mentions.append(entity_split[0])
            pages.append(entity_split[0].capitalize())
            par = par.replace(replace_str, entity_split[0])
        if len(entity_split) == 2:
            replace_str = "[[" + entity + "]]"
            mentions.append(entity_split[1])
            pages.append(entity_split[0].capitalize())
            par = par.replace(replace_str, entity_split[1])
    par = re.sub(r"(<ref>|</ref>|ref name|ref|\(\)|\( \))", "", par)
    par = par.replace("  ", " ")
    return par, mentions, pages


def preprocess_news(news):
    news_list = []
    for elem in news:
        new_content_list = []
        title = elem.get("title", "")
        content = elem.get("content", "")
        if title and content:
            replace_elements = re.findall(r"\[([\d]+ chars)]", content)
            for replace_elem in replace_elements:
                content = content.replace(f"[{replace_elem}]", "")
            content = content.replace("...", "").strip()
            content_list = content.split("\n")
            cur_len = 0
            max_len = 30
            cur_chunk = []
            for sentence in content_list:
                tokens = re.findall(re_tokenizer, sentence)
                if cur_len + len(tokens) < max_len:
                    cur_chunk.append(sentence)
                    cur_len += len(tokens)
                else:
                    new_content_list.append([" ".join(cur_chunk).strip(), False])
                    cur_chunk = [sentence]
                    cur_len = len(tokens)
            if cur_chunk:
                new_content_list.append([" ".join(cur_chunk).strip(), False])
            if new_content_list:
                news_list.append({"title": title, "content": new_content_list[:5]})
    return news_list
