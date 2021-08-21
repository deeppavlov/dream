#!/usr/bin/env python

import logging
import time
import re
import random
import json
import collections
import itertools

from flask import Flask, request, jsonify
from os import getenv
import sentry_sdk


sentry_sdk.init(getenv("SENTRY_DSN"))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

fun_facts_about_oscar_2020 = json.load(open("./content/fun_facts_about_oscar_2020.json"))
fun_facts_about_oscar_2019 = json.load(open("./content/fun_facts_about_oscar_2019.json"))


@app.route("/respond", methods=["POST"])
def respond():
    st_time = time.time()
    last_utter_batch = request.json["sentences"]
    responses = []

    for last_utter in last_utter_batch:
        response_text, confidence = dialog_segment_handler(last_utter)
        logger.info(f"Last_utter = {last_utter}")
        logger.info(f"Response_text = {response_text}")

        responses.append((response_text, confidence))

    total_time = time.time() - st_time
    logger.info(f"oscar exec time = {total_time:.3f}s")
    return jsonify(responses)


ANY_PATTERN = r"(['a-zA-z ]+)?"


def add_ANY_PATTERN(ordered_key_regs):
    regs = ANY_PATTERN.join(ordered_key_regs)
    return regs


def and_merge_regs(regs):
    regs = [and_merge_regs(reg) for reg in regs] if isinstance(regs[0], (list, tuple)) else regs
    assert isinstance(regs[0], str)
    if len(regs) > 1:
        return ".*".join([f"({reg})" for reg in regs])
    elif len(regs) == 1:
        return regs[0]
    raise "Unallowed segment regs"


def or_merge_regs(regs):
    regs = [or_merge_regs(reg) for reg in regs] if isinstance(regs[0], (list, tuple)) else regs
    assert isinstance(regs[0], str)
    if len(regs) > 1:
        return "|".join([f"({reg})" for reg in regs])
    elif len(regs) == 1:
        return regs[0]
    raise "Unallowed segment regs"


def compile_regs(dictionary):
    for key in dictionary.keys():
        # logger.info(f"key = {key}, dictionary[key] = {dictionary[key]}")
        dictionary[key] = re.compile(dictionary[key])
    return dictionary


# bag-of-words
def create_bow(regs, add_any_pattern=True):
    regs = itertools.permutations(regs, len(regs))
    regs = [and_merge_regs(reg) for reg in regs] if add_any_pattern else regs
    return or_merge_regs(list(regs))


dialog_segment_regs = collections.OrderedDict()
dialog_segment_candidates = collections.OrderedDict()
#  ordered by priority


def template_regs(filling_data: dict):
    regs = {}
    for k, v in filling_data.items():
        adds = v.get("adds", [r"(movi|academy.*awards|oscar|cinem|film)"])
        regs[k] = or_merge_regs([create_bow(adds + _reg) for _reg in v["regs"]])
        if v.get("aggressive"):
            regs[f"aggressive_{k}"] = or_merge_regs([create_bow(_reg) for _reg in v["regs"]])
    return regs


def template_cands(filling_data: dict):
    cands = {}
    for k, v in filling_data.items():
        cands[k] = v["candidates"]
        cands[f"aggressive_{k}"] = v["candidates"]
    return cands


# directors
# martin scorsese – the irishman
# todd phillips – joker
# sam mendes – 1917
# quentin tarantino – once upon a time in hollywood
# bong joonho – parasite
directors = collections.OrderedDict()
directors["director_scorsese"] = {
    "candidates": [
        utt
        for utt in "<SPLIT_POINT>Here is the fact about Martin Scorsese from hollywood.com: ".join(
            [
                "",
                "When Martin is directing Robert De Niro, the set is closed to all outsiders.",
                "Martin worked as a news editor at TV network CBS after graduating NYU.",
                "Martin is such a big music fan, he’s rarely without an iPod.",
                "Fawlty Towers is one of his all-time favorite TV shows.",
            ]
        ).split("<SPLIT_POINT>")
        if utt
    ],
    "aggressive": True,
    "regs": [[r"scorsese"]],
}
directors["director_mendes"] = {
    "candidates": [
        utt
        for utt in "<SPLIT_POINT>Here is the fact about sam mendes from uselessdaily.com: ".join(
            [
                "",
                "sam's full name is Sir Samuel Alexander Mendes CBE",
                "Sam was born on August 1, 1965",
                "Sam is best known for his directoral debut film American Beauty (1999)",
                "Sam also is known for dark re-inventions of the stage musicals Cabaret (1994), "
                "Oliver! (1994), Company (1995), and Gypsy (2003)",
            ]
        ).split("<SPLIT_POINT>")
        if utt
    ],
    "aggressive": True,
    "regs": [[r"mendes"]],
}
directors["director_tarantino"] = {
    "candidates": [
        utt
        for utt in "<SPLIT_POINT>Here is the fact about quentin tarantino from ifc.com: ".join(
            [
                "",
                "His career began in the late 1980s, when he wrote and directed My Best Friend’s Birthday, the"
                " screenplay which formed the basis for True Romance.",
                "In 2005, Tarantino was included on the annual"
                " Time 100 list of the most influential people in the world.",
                "Filmmaker and historian Peter Bogdanovich has called Tarantino, the single most influential"
                " director of his generation.",
                "In December 2015, Tarantino received a star on the Hollywood Walk of Fame for his contributions to"
                " the film industry.",
                "Tarantino was born in Knoxville, Tennessee, the only child of Connie McHugh and Tony Tarantino.",
                "His father is of Italian descent, and his mother has Cherokee and Irish ancestry.",
                "He was named for Quint Asper, Burt Reynolds’ character in the CBS series Gunsmoke.",
                "Tarantino’s mother allowed him to see movies with adult content, such as Carnal Knowledge and"
                " Deliverance.",
                "At 14 years old, Tarantino wrote one of his earliest works, a screenplay called Captain Peachfuzz"
                " and the Anchovy Bandit, where a thief steals pizzas from a pizzeria.",
                "At about 15 or 16, Tarantino dropped out of Narbonne High School in Harbor City, Los Angeles.",
                "He got a job ushering at a porn theater in Torrance, called the Pussycat Theater, after lying"
                " about his age.",
                "He worked as a recruiter in the aerospace industry, and for five years, he worked in Video"
                " Archives, a video store in Manhattan Beach, California.",
            ]
        ).split("<SPLIT_POINT>")
        if utt
    ],
    "aggressive": True,
    "regs": [[r"tarantino"]],
}
directors["director_bong"] = {
    "candidates": [
        utt
        for utt in "<SPLIT_POINT>Here is the fact about bong joonho from uselessdaily.com: ".join(
            [
                "",
                "Bong Joon-ho was born on September 14, 1969",
                "Bong Joon-ho is a South Korean film director and screenwriter",
                "Bong Joon-ho garnered international acclaim for his second feature film Memories of Murder (2003)",
                "Parasite also won Best Foreign Language Film at the 77th Golden Globe Awards",
                "Bong Joon-ho is the youngest of four children",
                "Bong's father was a graphic and industrial graphic designer, art director of the National Film"
                " Production and professor Bong Sang-gyun",
            ]
        ).split("<SPLIT_POINT>")
        if utt
    ],
    "aggressive": True,
    "regs": [[r"bong.*joonho"]],
}
directors["director_phillips"] = {
    "candidates": [
        utt
        for utt in "<SPLIT_POINT>Here is the fact about todd phillips from uselessdaily.com: ".join(
            [
                "",
                "Todd Phillips is an American filmmaker and actor",
                "Todd Phillips is best known for writing and directing the comedy films Road Trip (2000), Old"
                " School (2003), "
                "Starsky & Hutch (2004), The Hangover Trilogy (2009, 2011, and 2013) and Due Date (2010)",
                "For his work on the satirical comedy film Borat (2006), Phillips was nominated for "
                "the Academy.*Award for Best Adapted Screenplay",
                "Directing biographical crime film War Dogs (2016) and the psychological thriller" " film Joker (2019)",
                "Phillips was born in Brooklyn, New York City",
            ]
        ).split("<SPLIT_POINT>")
        if utt
    ],
    "aggressive": True,
    "regs": [[r"todd.*phillips"]],
}
dialog_segment_regs.update(template_regs(directors))
dialog_segment_candidates.update(template_cands(directors))

# actors
# antonio banderas – pain and glory as salvador mallo #is miss
# leonardo dicaprio – once upon a time in hollywood as rick dalton
# joaquin phoenix – joker as arthur fleck / joker
# tom hanks – a beautiful day in the neighborhood as fred rogers
# brad pitt – once upon a time in hollywood as cliff booth

actors = collections.OrderedDict()
actors["actor_pitt"] = {
    "candidates": [
        utt
        for utt in "<SPLIT_POINT>Here is the fact about brad pitt from thefactsite.com: ".join(
            [
                "",
                "His full name is William Bradley Pitt.",
                "brad pitt was born on 18th December, in 1963.",
                "brad pitt originates from Oklahoma, in the United States.",
                "brad pitt has two younger siblings; Douglas and Julie.",
                "brad pitt majored in journalism, at the University of Missouri.",
                "brad pitt stands at 5’11”.",
            ]
        ).split("<SPLIT_POINT>")
        if utt
    ],
    "aggressive": True,
    "regs": [[r"brad.*pitt"]],
}
actors["actor_joker"] = {
    "candidates": [
        utt
        for utt in "<SPLIT_POINT>Here is the fun fact about joaquin phoenix from brightside.me: ".join(
            [
                "",
                "Throughout his career, joaquin phoenix has appeared in more than 30 films.",
                "joaquin phoenix is been vegan since he was 3.",
                "At age 6, joaquin phoenix changed his name to Leaf.",
                "joaquin phoenix worked as a firefighter for a whole month to practice for a role.",
                "joaquin phoenix had to lose almost 45 pounds to play the Joker.",
                "His brother, River Phoenix, also began working as an actor whenjoaquin phoenix he was a child.",
                "joaquin phoenix won a Grammy for his portrayal of Johnny Cash.",
                "joaquin phoenix has been nominated for an Oscar 3 times.",
                "joaquin phoenix played Max in SpaceCamp.",
                "joaquin phoenix produced the documentary, What the Health.",
            ]
        ).split("<SPLIT_POINT>")
        if utt
    ],
    "aggressive": True,
    "regs": [[r"joaquin.*phoenix"], [r"joker.*actor"]],
}
actors["actor_dicaprio"] = {
    "candidates": [
        utt
        for utt in "<SPLIT_POINT>Here is the fact about leonardo dicaprio from justfunfacts.com: ".join(
            [
                "",
                "His full name is Leonardo Wilhelm DiCaprio.",
                "leonardo dicaprio was born on November 11, 1974 in Los Angeles, California.",
                "Leonardo is the only child of Irmelin, a legal secretary, and George DiCaprio, an underground"
                " comics artist and producer/distributor of comic books.",
                "From an early age he discovered a love of acting while living in some of the poorer areas of LA.",
                "DiCaprio dropped out of high school in his junior year, choosing to attend a free drama school"
                " and pursue his acting instead.",
                "DiCaprio makes an average of $20 million a year, with some years better than others.",
                "Leonardo DiCaprio has an estimated net worth of $245 million.",
            ]
        ).split("<SPLIT_POINT>")
        if utt
    ],
    "aggressive": True,
    "regs": [[r"dicaprio"]],
}
actors["actor_hanks"] = {
    "candidates": [
        utt
        for utt in "<SPLIT_POINT>Here is the fact about tom hanks from tonsoffacts.com: ".join(
            [
                "",
                "Hanks starred in the Robert Langdon film series, and voices Sheriff Woody in the Toy Story movie"
                " series.",
                "His movies have grossed more than $4.5 billion at U.S. and Canadian box offices"
                " and more than $9 billion worldwide, making him the third highest grossing actor in"
                " North America.",
                "He won a Golden Globe Award and an Academy.*Award for Best Actor for his role in Philadelphia,"
                " as well as a Golden Globe, an Academy.*Award, a Screen Actors Guild Award, and"
                " a People’s Choice Award for Best Actor for Forrest Gump.",
                "In 1995, Hanks became one of only two actors who won the Academy.*Award for Best Actor in"
                " consecutive years, with Spencer Tracy being the other.",
                "In 2004, Hanks received the Stanley Kubrick Britannia Award for Excellence in Film from"
                " the British Academy of Film and Television Arts.",
                " In 2014, Hanks received a Kennedy Center Honor and, in 2016, he received"
                " the Presidential Medal of Freedom from President Barack Obama, as well as"
                " the French Legion of Honor.",
            ]
        ).split("<SPLIT_POINT>")
        if utt
    ],
    "aggressive": True,
    "regs": [[r"tom.*hanks"]],
}
dialog_segment_regs.update(template_regs(actors))
dialog_segment_candidates.update(template_cands(actors))
# actress
# laura dern – marriage story as nora fanshaw
# scarlett johansson – jojo rabbit as rosie betzler
# jennifer lopez - hustlers as ramona vega
# florence pugh – little women as amy march
# margaret qualley - once upon a time in hollywood as pussycat
actresses = collections.OrderedDict()
actresses["actress_dern"] = {
    "candidates": [
        utt
        for utt in "<SPLIT_POINT>Here is the fact about laura dern from 10-facts-about.com: ".join(
            [
                "",
                "Both of Laura’s parents, father Bruce Dern and mother Diane Ladd, were successful actors."
                " Initially, they both had discouraged her from acting in films, but eventually gave in.",
                "Her cameo appearance in the 1973 Diane Ladd starrer, “White Lightening” was her film debut.",
                "She received the Miss Golden Globe award in 1982." " She was the youngest winner of this award, ever.",
                "Dern has acted in 2 films that were titled “Happy Endings”."
                " One was a 1983-made television film while the other was a 2005-made independent one.",
            ]
        ).split("<SPLIT_POINT>")
        if utt
    ],
    "aggressive": True,
    "regs": [[r"laura.*dern"]],
}
actresses["actress_johansson"] = {
    "candidates": [
        utt
        for utt in "<SPLIT_POINT>Here is the fact about scarlett johansson from boomsbeat.com: ".join(
            [
                "",
                "Scarlett Johansson has a twin brother named Hunter. They were born on November 22,"
                " 1984 but she is still technically the older sister after being born three minutes earlier"
                " than him.",
                "Johansson attended the famed Manhattan Professional Children's School. The school claims"
                " a number of stars among its graduates, including stars like Carrie Fisher and"
                " Sarah Michelle Gellar.",
                "Her father Karsten Johansson, a New York architect, and mother Melanie Sloan, her manager,"
                " now divorced, separated when she was 13.",
                "Her older sister Vanessa Johansson is also an actress.",
                "Her first movie was at age 9 in Rob Reiner's North. Scarlett went on to star in"
                " The Horse Whisperer and Lost In Translation to Eight Legged Freaks and"
                " Girl with a Pearl Earring.",
                "Johansson landed her first television appearance at the age of 8 when she appeared in a skit on"
                " Late Night With Conan O'Brian in 1993.",
                "Even though she's an internationally recognized sex-symbol, Scarlett chose to celebrate her"
                " 20th birthday at Disneyland.",
                "Her favorite movie is Willy Wonka & the Chocolate Factory.",
                "Johansson has been smoking since was 15 years old and can't seem to kick the habit.",
                "Her media nickname is ScarJo and she hates it! Johansson said in an interview that she finds"
                " the name 'awful.'",
                "Johansson is left-handed.",
            ]
        ).split("<SPLIT_POINT>")
        if utt
    ],
    "aggressive": True,
    "regs": [[r"johansson"]],
}
actresses["actress_pugh"] = {
    "candidates": [
        utt
        for utt in "<SPLIT_POINT>Here is the fact about florence pugh from uselessdaily.com: ".join(
            [
                "",
                "Her full name is Florence Rose C. M. Pugh",
                "Pugh was born on January 3 1996",
                "She made her professional acting debut in the mystery film The Falling (2014)",
                "Pugh portrayed Elizabeth de Burgh in the Netflix historical film Outlaw King (2018)",
                "Pugh has three siblings",
                "Pugh lived in the Spanish community of Andalusia for part of her childhood",
                "Her love of accents and comedy was first displayed at age six at Cokethorpe School in Hardwick,"
                " Oxfordshire",
            ]
        ).split("<SPLIT_POINT>")
        if utt
    ],
    "aggressive": True,
    "regs": [[r"florence.*pugh"]],
}
actresses["actress_qualley"] = {
    "candidates": [
        utt
        for utt in "<SPLIT_POINT>Here is the fact about margaret qualley from uselessdaily.com: ".join(
            [
                "",
                "margaret qualley was born on October 23th, 1994.",
                "The young actress was born in Montana.",
                "margaret qualley is the daughter of Andie MacDowell and Paul Qualley. Now you know were"
                " she gets her good looks from!",
                "margaret qualley has an older brother, Justin and an older sister, Rainey.",
                "margaret qualley grew up, as a teenager, in Asheville, North Carolina.She and"
                " her sister were both debutantes, and she made her debut at the Bal des débutantes in Paris.",
                "margaret qualley made her modeling debut at the age of 16 during New York Fashion Week,"
                " walking for Alberta Ferretti, in 2011.",
            ]
        ).split("<SPLIT_POINT>")
        if utt
    ],
    "aggressive": True,
    "regs": [[r"margaret.*qualley"]],
}
dialog_segment_regs.update(template_regs(actresses))
dialog_segment_candidates.update(template_cands(actresses))


# films
# Ford v Ferrari – Peter Chernin, Jenno Topping, and James Mangold
# The Irishman – HHHHHHHHH, RobeWWWWWWWW Niro, Jane Rosenthal, and Emma Tillinger Koskoff
# Jojo Rabbit – Carthew Neal, Taika Waititi, and Chelsea Winstanley
# Joker – Todd Phillips, Bradley Cooper, and Emma Tillinger Koskoff
# Little Women – Amy Pascal
# Marriage Story – Noah Baumbach and David Heyman
# 1917 – Sam Mendes, Pippa Harris, Jayne-Ann Tenggren, and Callum McDougal
# Once Upon a Time in Hollywood – David Heyman, Shannon McIntosh, and Quentin Tarantino
# Parasite – Kwak Sin-ae and Bong Joon-ho

films = collections.OrderedDict()
films["film_ford"] = {
    "candidates": [
        utt
        for utt in "<SPLIT_POINT>Here is the fact about Ford v Ferrari from uselessdaily.com: ".join(
            [
                "",
                "Ford v Ferrari is a 2019 American sports drama film",
                "The movie is titled Le Mans ’66 in the UK and other territories",
                "Ford v Ferrari is directed by James Mangold",
                "Ford v Ferrari is written by Jez Butterworth, John-Henry Butterworth, and Jason Keller",
                "Ford v Ferrari stars Matt Damon and Christian Bale",
                "Led by automotive visionary Carroll Shelby and his British driver, Ken Miles",
                "Filming began in July 2018 in California",
            ]
        ).split("<SPLIT_POINT>")
        if utt
    ],
    "aggressive": True,
    "regs": [[r"ford", r"ferrari"]],
}
films["film_jojo"] = {
    "candidates": [
        utt
        for utt in "<SPLIT_POINT>Here is the fact about Jojo Rabbit from wikipedia: ".join(
            [
                "",
                "Jojo Rabbit is a 2019 American comedy-drama film written and directed by Taika Waititi,"
                " based on Christine Leunens's book Caging Skies.",
                "Jojo Rabbit was chosen by the National Board of Review and the American Film Institute"
                " as one of the ten best films of the year.",
                "Roman Griffin Davis portrays the title character, Johannes 'Jojo' Betzler,"
                " a Hitler Youth member who finds out his mother is hiding a Jewish girl in their attic",
            ]
        ).split("<SPLIT_POINT>")
        if utt
    ],
    "aggressive": True,
    "regs": [[r"jojo.*rabbit"]],
}
films["film_women"] = {
    "candidates": [
        utt
        for utt in "<SPLIT_POINT>Here is the fact about Little Women from wikipedia: ".join(
            [
                "",
                "Little Women is a 2019 American coming-of-age period drama film written and directed by"
                " Greta Gerwig",
                "It is the seventh film adaptation of the 1868 novel of the same name by Louisa May Alcott.",
                "Little Women had its world premiere at the Museum of Modern Art in New York City on December 7,"
                " 2019, and was released theatrically in the United States on December 25, 2019,"
                " by Sony Pictures Releasing. ",
                "The film received critical acclaim, and has grossed over $164 million worldwide. ",
            ]
        ).split("<SPLIT_POINT>")
        if utt
    ],
    "aggressive": True,
    "regs": [[r"little.*women"]],
}
films["film_irishman"] = {
    "candidates": [
        utt
        for utt in "<SPLIT_POINT>Here is the fact about The Irishman from uselessdaily.com: ".join(
            [
                "",
                "The Irishman is a 2019 American epic crime film",
                "The Irishman is directed and produced by Martin Scorsese",
                "The Irishman written by Steven Zaillian",
                "The Irishman is based on the 2004 book I Heard You Paint Houses by Charles Brandt",
                "The film follows Frank “The Irishman” Sheeran (Robert De Niro),"
                " a truck driver who becomes a hitman and gets involved with mobster Russell Bufalino (Joe Pesci)"
                " and his crime family, including his time working for the powerful"
                " Teamster Jimmy Hoffa (Al Pacino)",
                "In September 2014, after years of development hell, The Irishman was announced"
                " as Scorsese’s next film following Silence (2016)",
                "The Irishman had its world premiere at the 57th New York Film Festival on September 27, 2019",
                "The Irishman is the story of Frank Sheeran, a mob hitman and"
                " World War II veteran who develops his skills during his service in Italy",
            ]
        ).split("<SPLIT_POINT>")
        if utt
    ],
    "aggressive": False,
    "regs": [[r"irishman"]],
}
films["film_joker"] = {
    "candidates": [
        utt
        for utt in "<SPLIT_POINT>Here is the fact about joker from boredpanda.com: ".join(
            [
                "",
                "Joker's Actor Joaquin Phoenix Based His Laugh On Videos Of"
                " People Suffering From Pathological Laughter",
                "Before Filming, The Director Phillips Told Joaquin Phoenix That He Envisioned Joker's Laughter"
                " As Something That's Almost Painful",
                "For The Role Of Joker, Actor Joaquin Phoenix Went On Grueling A Diet And Lost 52 Pounds",
                "The Bathroom Dance Was Improvised On The Spot By Joaquin Phoenix",
                "Joaquin Phoenix And The Late Heath Ledger Were Good Friends",
                "The Movie Is Based In 1981 Which Was Done Deliberately",
                "There Are At Least 3 Different Laughs The Joker Does: The 'Affliction' Laugh, The 'One Of"
                " The Guys Laugh, And The 'Authentic Joy' Laugh At The End",
                "Joker Cracked Imdb's 'Top 10 Highest-Rated Movies Of All Time' List",
                "When Preparing For The Role, Phoenix Studied The Movements Of Iconic Silent Film"
                " Stars Like Buster Keaton And Ray Bolger",
                "Joker Stairs Is Now A Thing On Google Maps And Fans Put It Into"
                " The 'Religious Destination' Category",
                "Many Past films Went To Dark Places Irl To Play The Role Of The Joker,"
                " But Phoenix Says He Didn't Have That Experience",
                "The Silent Film 'The Man Who Laughs' Was Also Another Major Influence On The New Joker Movie",
            ]
        ).split("<SPLIT_POINT>")
        if utt
    ],
    "aggressive": True,
    "regs": [[r"joker"]],
}
films["film_parasite"] = {
    "candidates": [
        utt
        for utt in "<SPLIT_POINT>Here is the fact about parasite from cosmo.ph: ".join(
            [
                "",
                "Parasite is a dark comedy, mystery, thriller film. ",
                "It had its world premiere at the prestigious 2019 Cannes Film Festival. ",
                "Choi Woo Shik recorded an original song for the film's soundtrack. ",
                "The script was originally written as a play!",
            ]
        ).split("<SPLIT_POINT>")
        if utt
    ],
    "aggressive": False,
    "regs": [[r"parasite"]],
}
films["film_marriage_story"] = {
    "candidates": [
        utt
        for utt in "<SPLIT_POINT>Here is the fact about Marriage Story from uselessdaily.com: ".join(
            [
                "",
                "The film follows a married couple going through a coast-to-coast divorce",
                "Filming took place in Los Angeles and New York City between January and"
                " April of the following year",
                "Followed by digital streaming on December 6, by Netflix",
                "The idea for the film first came to Baumbach in 2016, while in post-production on"
                " The Meyerowitz Stories",
                "Marriage Story had its world premiere at the Venice Film Festival on August 29, 2019",
            ]
        ).split("<SPLIT_POINT>")
        if utt
    ],
    "aggressive": True,
    "regs": [[r"marriage.*story"]],
}
films["film_nineteen_seventeen"] = {
    "candidates": [
        utt
        for utt in "<SPLIT_POINT>Here is the fact about 1917 from uselessdaily.com: ".join(
            [
                "",
                "1917 is a 2019 epic war film",
                "1917 is directed and produced by Sam Mendes",
                "The film is based in part on an account told to Mendes by his paternal grandfather, Alfred Mendes",
                "1917 was theatrically released in the United States and Canada on 25 December 2019 by"
                " Universal Pictures",
            ]
        ).split("<SPLIT_POINT>")
        if utt
    ],
    "aggressive": True,
    "regs": [[r"nineteen.*seventeen"]],
}
films["film_hollywood"] = {
    "candidates": [
        utt
        for utt in "<SPLIT_POINT>Here is the fact about Once Upon a Time in Hollywood from"
        " uselessdaily.com: ".join(
            [
                "",
                "Before Editing, the Film Was 4 Hours and 30 Minutes",
                "It is written and directed by Quentin Tarantino",
                "The film stars Leonardo DiCaprio, Brad Pitt and Margot Robbie",
                "The film is set in 1960s Los Angeles",
                "The film is the first of Tarantino’s not to be associated with producer Harvey Weinstein",
            ]
        ).split("<SPLIT_POINT>")
        if utt
    ],
    "aggressive": True,
    "regs": [[r"once.*time.*hollywood"]],
}
dialog_segment_regs.update(template_regs(films))
dialog_segment_candidates.update(template_cands(films))


oscars = collections.OrderedDict()
oscars["oscar_nomination_best_pic"] = {
    "candidates": ["in the nomination the best picture won the film parasite "],
    "aggressive": True,
    "regs": [[r"best", r"(movi|cinem|film|pic)"]],
}
oscars["oscar_nomination_best_director"] = {
    "candidates": ["in the nomination the best director won the director bong joon ho "],
    "aggressive": True,
    "regs": [[r"best", r"director"]],
}
oscars["oscar_nomination_best_actor"] = {
    "candidates": ["in the nomination the best actor won the actor joaquin phoenix "],
    "aggressive": True,
    "regs": [[r"best", r"actor"]],
}
oscars["oscar_nomination_best_actress"] = {
    "candidates": ["in the nomination the best actress won the actress renée zellweger "],
    "aggressive": True,
    "regs": [[r"best", r"actress"]],
}
oscars["oscar_nomination"] = {
    "candidates": ["in the nomination the best picture won the film parasite "],
    "aggressive": True,
    "regs": [[r"nominat"]],
}
oscars["oscar_2019"] = {
    "candidates": fun_facts_about_oscar_2019,
    "aggressive": False,
    "regs": [[r"((two thousand nineteen)|twenty nineteen)"]],
    "adds": [r"(academy.*awards|oscar)"],
}
oscars["oscar_2020"] = {
    "candidates": fun_facts_about_oscar_2020,
    "aggressive": False,
    "regs": [[r"((two thousand twenty)|twenty twenty)"]],
    "adds": [r"(academy.*awards|oscar)"],
}
oscars["who_win"] = {
    "candidates": [
        "i think all candidates had good chances, "
        "in the nomination the best picture won the film parasite "
        "in the nomination the best director won the director bong joon ho "
        "in the nomination the best actor won the actor brad pitt "
        "in the nomination the best actress won the actress renée zellweger "
    ],
    "aggressive": False,
    "regs": [[r"(who)", r"(win|make|won)", r"((two thousand twenty)|twenty twenty)"], [r"(who)", r"(win|make|won)"]],
    "adds": [r"(academy.*awards|oscar)"],
}
oscars["oscar"] = {
    "candidates": fun_facts_about_oscar_2020,
    "aggressive": False,
    "regs": [[r".*"]],
    "adds": [r"(academy.*awards|oscar)"],
}
dialog_segment_regs.update(template_regs(oscars))
dialog_segment_candidates.update(template_cands(oscars))

dialog_segment_regs = compile_regs(dialog_segment_regs)


def dialog_segment_handler(last_utter):
    response = ""
    confidence = 0.0
    curr_user_uttr = last_utter.lower()

    active_segments = [
        segment_name for segment_name, segment_reg in dialog_segment_regs.items() if segment_reg.search(curr_user_uttr)
    ]
    logger.info(f"active_segments = {active_segments}")
    if active_segments:
        response = random.choice(dialog_segment_candidates[active_segments[0]])
        confidence = 1.0 if len(active_segments) > 1 else 0.8
    return response, confidence


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)
