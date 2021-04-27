import itertools
import random

used_types_dict = [{"types": ["Q11253473"  # smart device
                              ],
                    "titles": {"history": "", "hardware": "", "software": ""}},
                   {"entity_substr": ["hiking"],
                    "titles": {"equipment": "", "destinations": ""}},
                   {"types": ["Q15707583",  # fictional animal (for example, unicorn)
                              "Q2239243"  # mythical creature
                              ],
                    "titles": {"mythology": "", "heraldry": "", "history": "", "modern depictions": "", "origin": "",
                               "popular culture": "Would you like to know about {} in popular culture?"}},
                   {"entity_substr": ["medicine"],
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
                               "culture": "Would you like to know about {} in popular culture?"}}
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


def if_switch_wiki_skill(user_uttr_annotations):
    flag = False
    wp_output = user_uttr_annotations.get("wiki_parser", {})
    if isinstance(wp_output, dict):
        entities_info = wp_output.get("entities_info", {})
        for entity, triplets in entities_info.items():
            types = triplets.get("types", []) + triplets.get("instance of", []) + triplets.get("subclass of", [])
            type_ids = [elem for elem, label in types]
            inters = set(type_ids).intersection(used_types)
            if inters:
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
                    if rand_title == title.lower() and rand_title != prev_title:
                        found_title = rand_title
                        found_page_title = title
                        found = True
                        break
                if not found:
                    for title in all_titles:
                        if rand_title in title.lower() and rand_title != prev_title:
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
                if title.lower() == chosen_title:
                    paragraphs = find_par(topic_facts[title])
                    return paragraphs
                else:
                    paragraphs = find_paragraph(topic_facts[title], chosen_title)
                    if paragraphs:
                        return paragraphs
    return paragraphs
