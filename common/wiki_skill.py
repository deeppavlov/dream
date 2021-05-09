import itertools
import random
import re
from common.universal_templates import COMPILE_WHAT_TO_TALK_ABOUT
from common.animals import ANIMALS_FIND_TEMPLATE

used_types_dict = [{"types": ["Q11253473"  # smart device
                              ],
                    "titles": {"history": "", "hardware": "", "software": ""}},
                   {"entity_substr": ["hiking"],
                    "page_title": "Hiking",
                    "titles": {"equipment": "", "destinations": ""}},
                   {"types": ["Q15707583",  # fictional animal (for example, unicorn)
                              "Q2239243"  # mythical creature
                              ],
                    "titles": {"mythology": "", "heraldry": "", "history": "", "modern depictions": "", "origin": "",
                               "popular culture": "Would you like to know about {} in popular culture?"}},
                   {"entity_substr": ["medicine"],
                    "page_title": "Medicine",
                    "titles": {"clinical practice": "", "branches": "", "quality": "",
                               "traditinal medicine": "Would you like to know about traditional medicine?"}},
                   {"types": ["Q12140"  # medication
                              ],
                    "titles": {"medical use": "", "effect": "", "overdose": "",
                               "symptoms": "Would you like to know about the symptoms of {} usage?",
                               "treatment": "",
                               "culture": "Would you like to know about {} in culture?"}},
                   {"entity_substr": ["cars", "automobiles"],
                    "titles": {"autonomous car": "Would you like to know about autonomous car?",
                               "car sharing": "Would you like to know about car sharing?",
                               "mass production": "Would you like to know about cars in mass production?",
                               "environmental impact": ""}},
                   {"types": ["Q17737"  # theory (for example, quantum theory)
                              ],
                    "titles": {"fundamental concepts": "", "application": "", "formulation": "",
                               "relation": "Would you like to know about the relation of {} to other theories?",
                               "examples": ""}},
                   {"types": ["Q1587903",  # science
                              "Q11862829"  # academic discipline
                              ],
                    "titles": {"application": "", "research methods": "",
                               "themes": "Would you like to know about basic themes of {}?",
                               "major schools": "",
                               "relation": "Would you like to know about the relation of {} to other fields?",
                               "research fields": "", "core theories": ""}},
                   {"types": ["Q334166",  # transport
                              "Q752870"  # motor vehicle
                              ],
                    "titles": {"uses": "", "usage": "", "repair": "", "technical aspects": "", "parts": "",
                               "design": ""}},
                   {"types": ["Q7278"  # political party
                              ],
                    "titles": {"symbols": "", "ideology": "", "voter": "Would you like to know about voters of {}",
                               "structure": ""}},
                   {"types": ["Q16521"],  # taxon (species of animal)
                    "titles": {"distribution": "Would you like to know where {} live?",
                               "relationship with humans": "", "behavior": "", "behaviour": "",
                               "social structure": "",
                               "cultural": "Would you like to know about {} in popular culture?",
                               "culture": "Would you like to know about {} in popular culture?"}},
                   {"entity_substr": ["minecraft"],
                    "types": ["Q7889"],  # video game
                    "wikihow_info": {"Build-a-Wooden-House-in-Minecraft": ""},
                    "titles": {"game modes": "", "multiplayer": "", "customization": "", "awards": "",
                               "films": "Would you like to know about films based on {}?",
                               "virtual reality": "Would you like to know how {} can be played using virtual reality?",
                               }},
                   {"entity_substr": ["tiktok"],
                    "page_title": "TikTok",
                    "titles": {"viral trends": "", "users": "", "features": ""}},
                   {"entity_substr": ["artificial intelligence"],
                    "page_title": "Artificial intelligence",
                    "titles": {"natural language processing":
                               "Would you like to know about natural language processing?",
                               "knowledge representation":
                                   "Would you like to hear about knowledge representation in {}?",
                               "symbolic": "Are you interested in symbolic {}?",
                               "brain simulation": "Would you like to know about brain simulation?",
                               "applications": "", "risks": ""}},
                   {"types": ["Q1114461", "Q95074"],  # comics character, fictional character
                    "titles": {"personality": "", "skills": "", "early years": "", "conception": "", "voice": "",
                               "creation": "Would you like to learn how {} was created?", "character biography": ""
                               }},
                   {"entity_substr": ["politic", "politics"],
                    "page_title": "Politics",
                    "titles": {"forms of government": "Would you like to know about forms of government?",
                               "political culture": "Are you interested in political culture?",
                               "political corruption": "Do you want to hear about political corruption?",
                               "democracy": "Would you like to learn about democracy?", "ancient history": "",
                               "political conflict": "Do you want to hear about political conflicts?"}},
                   {"types": ["Q82955", "Q372436"],  # politician
                    "titles": {"political career": "", "early life": "", "family": "", "religious views": "",
                               "early years": "", "business career": "", "media career": "", "domestic policy": "",
                               "foreign policy": "", "election": "", "presidential campaign": "",
                               "political positions": "", "reputation": ""}},
                   {"entity_substr": ["robots", "robot"],
                    "page_title": "Robot",
                    "titles": {"mobile robot": "Would you like to learn about mobile robots?",
                               "service robot": "Would you like to hear about service robots?",
                               "military robot": "Do you want to learn about military robots?",
                               "factory robot": "Are you interested in factory robots?",
                               "literature": "Would you like to know about books about robots?",
                               "films": "Are you interested in films about robots?"}},
                   {"entity_substr": ["religion"],
                    "page_title": "Religion",
                    "titles": {"judaism": "Would you like to know about judaism?",
                               "christianity": "Do you want to learn about christianity?",
                               "islam": "Would you like to know about islam?",
                               "buddhism": "Would you like to know about buddhism?"}},
                   {"entity_substr": ["art", "arts"],
                    "page_title": "The arts",
                    "titles": {"architecture": "Would you like to know about architecture?",
                               "drawing": "Would you like to know about drawing?",
                               "painting": "Would you like to know about painting?",
                               "photography": "Would you like to know about photography?",
                               "sculpture": "Would you like to know about sculpture?",
                               "dance": "Would you like to know about dance?",
                               "theatre": "Would you like to know about theatre?"}},
                   {"entity_substr": ["dinosaur", "dinosaurs"],
                    "page_title": "Dinosaur",
                    "titles": {"behavior": "", "pre-scientific history": "",
                               "early dinosaur research": "Would you like to learn about early research of dinosaurs?",
                               "discoveries": "", "origins and early evolution": ""}},
                   {"entity_substr": ["teleportation"],
                    "page_title": "Teleportation",
                    "titles": {"fiction": "Would you like to know about teleportation in fiction?",
                               "science": ""}},
                   {"types": ["Q198"],  # war
                    "titles": {"causes": "", "tactics": "", "general features": "", "diplomacy": "", "outbreak": "",
                               "battles": ""}},
                   {"types": ["Q105756498", "Q215380"],  # type of musical group, musical group
                    "titles": {"early years": "", "breakthrough success": "", "band split-up": "", "new line-up": "",
                               "successes and struggles": "", "musical style": "", "development": "", "influences": "",
                               "awards and achievements": "", "touring years": ""}},
                   {"entity_substr": ["space", "outer space"],
                    "page_title": "Space exploration",
                    "titles": {"first outer space flights": "", "first human outer space flight": "",
                               "first astronomical body space explorations": "", "first space station": "",
                               "first interstellar space flight": "", "deep space exploration": "",
                               "future of space exploration": ""}},
                   {"entity_substr": ["cryptocurrency"],
                    "page_title": "Cryptocurrency",
                    "titles": {"blockchain": "Would you like to know about blockchain?", "mining": "",
                               "darknet markets": "", "exchanges": ""}},
                   {"entity_substr": ["bitcoin"],
                    "page_title": "Bitcoin",
                    "titles": {"blockchain": "Would you like to know about blockchain?", "mining": "",
                               "darknet markets": "", "exchanges": "", "software implementation": "",
                               "transactions": ""}},
                   {"entity_substr": ["drawing"],
                    "page_title": "Drawing",
                    "titles": {"technique": "", "materials": "", "process": ""}},
                   {"entity_substr": ["fishing"],
                    "page_title": "Fishing",
                    "titles": {"traditional fishing": "", "recreational fishing": "", "techniques": ""}},
                   {"types": ["Q2066131"],  # athlete
                    "titles": {"club career": "", "international career": "", "player profile": "",
                               "personal life": ""}}
                   ]

used_types = set(itertools.chain.from_iterable([elem.get("types", []) for elem in used_types_dict]))
used_substr = set(itertools.chain.from_iterable([elem.get("entity_substr", []) for elem in used_types_dict]))
blacklist_words = {"yup", "true", "false"}

prohibited_topics = {"music", "films", "movies", "sport", "travel", "food", "animals", "pet", "pets", "coronavirus",
                     "corona virus", "gossip", "gossips"}
prohibited_types = {"Q571",  # book
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
                    "Q2095"  # food
                    }

QUESTION_TEMPLATES = ["Would you like to know about {} of {}?",
                      "Do you want to learn about {} of {}?",
                      "Are you interested in {} of {}?",
                      "Do you want to hear about {} of {}?"
                      ]

CONF_DICT = {"UNDEFINED": 0.0, "USER_QUESTION_IN_BEGIN": 0.8, "ENTITY_IN_HISTORY": 0.9, "WIKI_TYPE_DOUBT": 0.9,
             "OTHER_DFF_SKILLS": 0.9, "WIKI_TYPE": 0.94, "IN_SCENARIO": 0.95, "WIKI_TOPIC": 0.99}
WIKI_BLACKLIST = re.compile(r"(margin|\bfont\b|wikimedia|wikitable)", re.IGNORECASE)


def find_entity_wp(annotations):
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
    wp_output = annotations.get("wiki_parser", {})
    if isinstance(wp_output, dict):
        entities_info = wp_output.get("entities_info", {})
        for entity, triplets in entities_info.items():
            entity_id = triplets.get("plain_entity", "")
            types = triplets.get("types", []) + triplets.get("instance of", []) + triplets.get("subclass of", []) + \
                triplets.get("occupation", []) + triplets.get("types_2hop", [])
            type_ids = [elem for elem, label in types]
            inters = set(type_ids).intersection(used_types)
            in_not_used_types = set(type_ids).intersection(prohibited_types)
            in_not_used_topics = entity in prohibited_topics or entity in blacklist_words
            if inters and not in_not_used_topics and nounphr_label_dict.get(entity, "") != "number":
                found_entity_substr = entity
                found_entity_id = entity_id
                found_entity_types = inters
                found_animal = re.findall(ANIMALS_FIND_TEMPLATE, entity)
                conf_type = "WIKI_TYPE"
                if in_not_used_types or found_animal:
                    conf_type = "OTHER_DFF_SKILLS"
                break
        wiki_skill_entities_info = wp_output.get("wiki_skill_entities_info", {})
        if wiki_skill_entities_info:
            for entity, triplets in wiki_skill_entities_info.items():
                if entity not in prohibited_topics and nounphr_label_dict.get(entity, "") != "number":
                    entity_id = triplets.get("plain_entity", "")
                    types = triplets.get("types", []) + triplets.get("instance of", []) + \
                        triplets.get("subclass of", []) + triplets.get("occupation", []) + \
                        triplets.get("types_2hop", [])
                    type_ids = [elem for elem, label in types]
                    conf_type = "WIKI_TYPE"
                    pos = triplets["pos"]
                    if pos > 0:
                        conf_type = "WIKI_TYPE_DOUBT"
                    found_entity_substr = entity
                    found_entity_id = entity_id
                    found_entity_types = type_ids
                    break
    return found_entity_substr, found_entity_id, found_entity_types, conf_type


def find_entity_nounphr(annotations):
    found_entity_substr = ""
    conf_type = "UNDEFINED"
    nounphrases = annotations.get("cobot_entities", {}).get("labelled_entities", [])
    found = False
    for nounphr in nounphrases:
        nounphr_text = nounphr.get("text", "")
        nounphr_label = nounphr.get("label", "")
        in_not_used_substr = nounphr_text in prohibited_topics or nounphr_text in blacklist_words
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
                if re.findall(rf"\b{nounphr_text}\b", used_entity_substr, re.IGNORECASE) \
                        or re.findall(rf"\b{used_entity_substr}\b", nounphr_text, re.IGNORECASE) \
                        and not in_not_used_substr:
                    found_entity_substr = used_entity_substr
                    conf_type = "WIKI_TOPIC"
                    found = True
                    break
        if found:
            break

    return found_entity_substr, conf_type


def if_user_dont_know_topic(user_uttr, bot_uttr):
    flag = False
    what_to_talk_about = re.findall(COMPILE_WHAT_TO_TALK_ABOUT, bot_uttr.get("text", ""))
    user_dont_know = re.findall("(do not|dont|don't) know", user_uttr["text"]) \
        or re.findall("(anything|everything)", user_uttr["text"])
    if what_to_talk_about and user_dont_know:
        flag = True
    return flag


def if_switch_wiki_skill(user_uttr, bot_uttr):
    flag = False
    user_uttr_annotations = user_uttr["annotations"]
    found_entity_substr, found_entity_id, found_entity_types, conf_type_wp = find_entity_wp(user_uttr_annotations)
    found_entity_substr, conf_type_nounphr = find_entity_nounphr(user_uttr_annotations)
    user_dont_know = if_user_dont_know_topic(user_uttr, bot_uttr)
    asked_name = "what is your name" in bot_uttr.get("text", "").lower()
    asked_news = "news" in user_uttr["text"]
    if (found_entity_id or found_entity_substr or user_dont_know) and not asked_name and not asked_news:
        flag = True
    cobot_topics = user_uttr_annotations.get("cobot_topics", {}).get("text", [])
    decrease_conf_topic = "UNDEFINED"
    if "Food_Drink" in cobot_topics:
        decrease_conf_topic = "OTHER_DFF_SKILLS"
    all_confs = [(conf_type, CONF_DICT[conf_type]) for conf_type in [conf_type_wp, conf_type_nounphr,
                                                                     decrease_conf_topic]]
    all_confs = sorted(all_confs, key=lambda x: x[1], reverse=True)
    wiki_skill_conf_type = all_confs[0][0]
    return flag, wiki_skill_conf_type


def if_find_entity_in_history(dialog):
    flag = False
    all_user_uttr = dialog["human_utterances"]
    utt_num = len(all_user_uttr)
    if utt_num > 1:
        for i in range(utt_num - 2, 0, -1):
            annotations = all_user_uttr[i]["annotations"]
            found_entity_substr, found_entity_id, found_entity_types, _ = find_entity_wp(annotations)
            found_entity_substr, _ = find_entity_nounphr(annotations)
            if found_entity_id or found_entity_substr:
                flag = True
                break
    return flag


def choose_title(vars, all_titles, titles_we_use, prev_title, used_titles):
    found_title = ""
    found_page_title = ""
    if titles_we_use:
        for _ in range(len(all_titles)):
            found = False
            rand_title = random.choice(titles_we_use)
            if rand_title.lower() not in used_titles:
                for title in all_titles:
                    if rand_title.lower() == title.lower() and rand_title != prev_title:
                        found_title = rand_title
                        found_page_title = title
                        found = True
                        break
                if not found:
                    for title in all_titles:
                        if rand_title.lower() in title.lower() and rand_title != prev_title:
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
                if title.lower() not in used_titles:
                    found_title = title.lower()
                    found_page_title = title
    return found_title, found_page_title


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
        titles = list(topic_facts.keys())
        if "first_par" in titles:
            chosen_title = "first_par"
        else:
            chosen_title = random.choice(titles)
        return find_par(topic_facts[chosen_title])


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
        entity_split = entity.split('|')
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
    par = re.sub("(<ref>|</ref>|ref name|ref)", "", par)
    par = par.replace("  ", " ")
    return par, mentions, pages
