import itertools
import random
import re
from common.universal_templates import COMPILE_WHAT_TO_TALK_ABOUT

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
                               "science": ""}}
                   ]

used_types = set(itertools.chain.from_iterable([elem.get("types", []) for elem in used_types_dict]))
used_substr = set(itertools.chain.from_iterable([elem.get("entity_substr", []) for elem in used_types_dict]))

prohibited_topics = {"music", "films", "movies", "sport", "travel", "food", "animals", "pets"}
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


def find_entity_wp(annotations):
    found_entity_substr = ""
    found_entity_id = ""
    found_entity_types = []
    wp_output = annotations.get("wiki_parser", {})
    if isinstance(wp_output, dict):
        entities_info = wp_output.get("entities_info", {})
        for entity, triplets in entities_info.items():
            entity_id = triplets.get("plain_entity", "")
            types = triplets.get("types", []) + triplets.get("instance of", []) + triplets.get("subclass of", []) + \
                triplets.get("occupation", [])
            type_ids = [elem for elem, label in types]
            inters = set(type_ids).intersection(used_types)
            in_not_used_types = set(type_ids).intersection(prohibited_types)
            if inters and not in_not_used_types:
                found_entity_substr = entity
                found_entity_id = entity_id
                found_entity_types = inters
                break
    return found_entity_substr, found_entity_id, found_entity_types


def find_entity_nounphr(annotations):
    found_entity_substr = ""
    nounphrases = annotations.get("cobot_nounphrases", [])
    found = False
    for nounphr in nounphrases:
        in_not_used_substr = nounphr in prohibited_topics
        if nounphr in used_substr and not in_not_used_substr:
            found_entity_substr = nounphr
            break
        for used_entity_substr in used_substr:
            if (nounphr in used_entity_substr.lower() or used_entity_substr.lower() in nounphr) \
                    and not in_not_used_substr:
                found_entity_substr = used_entity_substr
                found = True
                break
        if found:
            break

    return found_entity_substr


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
    found_entity_substr, found_entity_id, found_entity_types = find_entity_wp(user_uttr_annotations)
    found_entity_substr = find_entity_nounphr(user_uttr_annotations)
    user_dont_know = if_user_dont_know_topic(user_uttr, bot_uttr)
    if found_entity_id or found_entity_substr or user_dont_know:
        flag = True
    return flag


def if_find_entity_in_history(dialog):
    flag = False
    all_user_uttr = dialog["human_utterances"]
    utt_num = len(all_user_uttr)
    if utt_num > 1:
        for i in range(utt_num - 2, 0, -1):
            annotations = all_user_uttr[i]["annotations"]
            found_entity_substr, found_entity_id, found_entity_types = find_entity_wp(annotations)
            found_entity_substr = find_entity_nounphr(annotations)
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
            if rand_title not in used_titles:
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
    return par, mentions, pages
