import common.constants as common_constants
from dff import GRAPH, RESPONSE, TRANSITIONS, GLOBAL_TRANSITIONS, PROCESSING
from dff import previous, forward
from common.speech_functions.generic_responses import (
    sys_response_to_speech_function_request as generic_responses_intent,
)
from common.dialogflow_framework.extensions import intents, custom, custom_functions, priorities, generic_responses
from common.dialogflow_framework.extensions.facts_utils import fact_provider
from common.dialogflow_framework.extensions.custom_functions import set_confidence_and_continue_flag
import logging
import re
import common.dialogflow_framework.utils.state as state_utils
from common.utils import is_yes
from common.wiki_skill import find_entity_by_types
from dff import Context, Actor, Node


def has_correct_answer(ctx: Context, actor: Actor, *args, **kwargs):
    flag = False
    a = ["Abbey Road", "A Hard Day's Night"]
    ar = "|".join(a)
    vars = ctx.shared_memory.get("vars", {})
    user_uttr = state_utils.get_last_human_utterance(vars)
    extracted_ar = re.findall(ar, user_uttr.get("text", ""), re.IGNORECASE)
    if extracted_ar:
        flag = True

    return flag


def has_album(ctx: Context, actor: Actor, *args, **kwargs):
    flag = False
    albums = ["Please Please Me", "With the Beatles", "Introducing... The Beatles", "Meet the Beatles!",
              "Twist and Shout", "The Beatles' Second Album", "The Beatles' Long Tall Sally", "A Hard Day's Night",
              "Something New", "Help!", "Sgt. Pepper's Lonely Hearts Club Band", "White Album", "The Beatles Beat",
              "Another Beatles Christmas Record", "Beatles '65", "Beatles VI", "Five Nights In A Judo Arena",
              "The Beatles at the Hollywood Bowl", "Live! at the Star-Club in Hamburg, German; 1962",
              "The Black Album", "20 Exitos De Oro", "A Doll's House", "The Complete Silver Beatles",
              "Rock 'n' Roll Music Vol. 1", "Yellow Submarine", "Let It Be", "Beatles for Sale",
              "Revolver", "Abbey Road", "Rubber Soul"]

    albums_re = "|".join(albums)
    vars = ctx.shared_memory.get("vars", {})
    user_uttr = state_utils.get_last_human_utterance(vars)
    extracted_album = re.findall(albums_re, user_uttr.get("text", ""), re.IGNORECASE)
    if extracted_album:
        flag = True

    return flag


def extract_albums(node_label: str, node: Node, ctx: Context, actor: Actor, *args, **kwargs):
    slot_values = ctx.shared_memory.get("slot_values", {})
    albums = ["Please Please Me", "With the Beatles", "Introducing... The Beatles", "Meet the Beatles!",
              "Twist and Shout", "The Beatles' Second Album", "The Beatles' Long Tall Sally", "A Hard Day's Night",
              "Something New", "Help!", "Sgt. Pepper's Lonely Hearts Club Band", "White Album", "The Beatles Beat",
              "Another Beatles Christmas Record", "Beatles '65", "Beatles VI", "Five Nights In A Judo Arena",
              "The Beatles at the Hollywood Bowl", "Live! at the Star-Club in Hamburg, German; 1962",
              "The Black Album", "20 Exitos De Oro", "A Doll's House", "The Complete Silver Beatles",
              "Rock 'n' Roll Music Vol. 1", "Yellow Submarine", "Let It Be", "Beatles for Sale",
              "Revolver", "Abbey Road", "Rubber Soul"]

    albums_re = "|".join(albums)
    vars = ctx.shared_memory.get("vars", {})
    user_uttr = state_utils.get_last_human_utterance(vars)
    extracted_album = re.findall(albums_re, user_uttr.get("text", ""), re.IGNORECASE)
    if extracted_album:
        slot_values["beatles_album"] = extracted_album[0]
        ctx.shared_memory["slot_values"] = slot_values

    return node_label, node


def has_songs(ctx: Context, actor: Actor, *args, **kwargs):
    flag = False
    songs = ["Hey Jude", "Don't Let Me Down", "We Can Work it Out", "Come Together",
             "Yellow Submarine", "Revolution", "Imagine", "Something", "Hello, Goodbye",
             "A Day In The Life", "Help!", "Penny Lane"]

    songs_re = "|".join(songs)
    vars = ctx.shared_memory.get("vars", {})
    user_uttr = state_utils.get_last_human_utterance(vars)
    extracted_song = re.findall(songs_re, user_uttr.get("text", ""), re.IGNORECASE)
    if extracted_song:
        flag = True

    return flag


def has_lennon(node_label: str, node: Node, ctx: Context, actor: Actor, *args, **kwargs):
    flag = False
    member = "John Lennon"
    vars = ctx.shared_memory.get("vars", {})
    user_uttr = state_utils.get_last_human_utterance(vars)
    extracted_member = re.findall(member, user_uttr.get("text", ""), re.IGNORECASE)
    if extracted_member:
        flag = True

    return flag


def has_mccartney(node_label: str, node: Node, ctx: Context, actor: Actor, *args, **kwargs):
    flag = False
    member = "Paul McCartney"
    vars = ctx.shared_memory.get("vars", {})
    user_uttr = state_utils.get_last_human_utterance(vars)
    extracted_member = re.findall(member, user_uttr.get("text", ""), re.IGNORECASE)
    if extracted_member:
        flag = True

    return flag


def has_starr(node_label: str, node: Node, ctx: Context, actor: Actor, *args, **kwargs):
    flag = False
    member = "Ringo Starr"
    vars = ctx.shared_memory.get("vars", {})
    user_uttr = state_utils.get_last_human_utterance(vars)
    extracted_member = re.findall(member, user_uttr.get("text", ""), re.IGNORECASE)
    if extracted_member:
        flag = True

    return flag


def has_harrison(node_label: str, node: Node, ctx: Context, actor: Actor, *args, **kwargs):
    flag = False
    member = "George Harrison"
    vars = ctx.shared_memory.get("vars", {})
    user_uttr = state_utils.get_last_human_utterance(vars)
    extracted_member = re.findall(member, user_uttr.get("text", ""), re.IGNORECASE)
    if extracted_member:
        flag = True

    return flag


def extract_members(node_label: str, node: Node, ctx: Context, actor: Actor, *args, **kwargs):
    slot_values = ctx.shared_memory.get("slot_values", {})
    members = ["John Lennon", "Ringo Starr", "Paul McCartney", "George Harrison"]

    members_re = "|".join(members)
    vars = ctx.shared_memory.get("vars", {})
    user_uttr = state_utils.get_last_human_utterance(vars)
    extracted_member = re.findall(members_re, user_uttr.get("text", ""), re.IGNORECASE)
    if extracted_member:
        slot_values["beatles_member"] = extracted_member[0]
        ctx.shared_memory["slot_values"] = slot_values

    return node_label, node


def extract_inst(node_label: str, node: Node, ctx: Context, actor: Actor, *args, **kwargs):
    slot_values = ctx.shared_memory.get("slot_values", {})
    insts = ["trumpet", "drums", "guitar"]
    insts_re = "|".join(insts)
    vars = ctx.shared_memory.get("vars", {})
    user_uttr = state_utils.get_last_human_utterance(vars)
    extracted_inst = re.findall(insts_re, user_uttr.get("text", ""), re.IGNORECASE)
    if extracted_inst:
        slot_values[extracted_inst[0]] = extracted_inst[0]
        ctx.shared_memory["slot_values"] = slot_values

    return node_label, node


def move_on(ctx: Context, actor: Actor, *args, **kwargs):
    flag = False
    move_on = "move on"
    vars = ctx.shared_memory.get("vars", {})
    user_uttr = state_utils.get_last_human_utterance(vars)
    extracted_mo = re.findall(move_on, user_uttr.get("text", ""), re.IGNORECASE)
    if extracted_mo:
        flag = True

    return flag


counter = 0


def not_visited_album(ctx: Context, actor: Actor, *args, **kwargs):
    flag = True
    counter += 1
    if counter == 12:
        flag = False
    return flag


def extract_albums(node_label: str, node: Node, ctx: Context, actor: Actor, *args, **kwargs):
    slot_values = ctx.shared_memory.get("slot_values", {})
    albums = ["Please Please Me", "With the Beatles", "Introducing... The Beatles", "Meet the Beatles!",
              "Twist and Shout", "The Beatles' Second Album", "The Beatles' Long Tall Sally", "A Hard Day's Night",
              "Something New", "Help!", "Sgt. Pepper's Lonely Hearts Club Band", "White Album", "The Beatles Beat",
              "Another Beatles Christmas Record", "Beatles '65", "Beatles VI", "Five Nights In A Judo Arena",
              "The Beatles at the Hollywood Bowl", "Live! at the Star-Club in Hamburg, German; 1962",
              "The Black Album", "20 Exitos De Oro", "A Doll's House", "The Complete Silver Beatles",
              "Rock 'n' Roll Music Vol. 1", "Yellow Submarine", "Let It Be", "Beatles for Sale",
              "Revolver", "Abbey Road", "Rubber Soul"]

    albums_re = "|".join(albums)
    vars = ctx.shared_memory.get("vars", {})
    user_uttr = state_utils.get_last_human_utterance(vars)
    extracted_album = re.findall(albums_re, user_uttr.get("text", ""), re.IGNORECASE)
    if extracted_album:
        slot_values["album_name"] = extracted_album[0]
        ctx.shared_memory["slot_values"] = slot_values

    return node_label, node


def enter_album(album_name: str, node_label: str, node: Node, ctx: Context, actor: Actor, *args, **kwargs):
    flag = False
    vars = ctx.shared_memory.get("vars", {})
    user_uttr = state_utils.get_last_human_utterance(vars)
    extracted_album = re.findall(album_name, user_uttr.get("text", ""), re.IGNORECASE)
    if extracted_album:
        flag = True
    return flag


def slot_filling_albums(node_label: str, node: Node, ctx: Context, actor: Actor, *args, **kwargs):
    slot_values = ctx.shared_memory.get("slot_values", {})
    slot_values['first_album'] = "Let's begin our trip here. I will show you some albums first. " \
                                 "If you get tired, just text me 'MOVE ON'"
    slot_values['a_hard_days_night_corr'] = "And you're right, A Hard Day's Night it was! "
    slot_values['a_hard_days_noght_wrong'] = "It was Hard Day's Night!"
    slot_values['rubber_soul'] = "However, it was after this cry for 'Help' that the Beatles became the Beatles."
    slot_values['yellow_submarine'] = "Then let's take a look at the album."
    slot_values['abbey_road'] = "By the way, The White Album' recording sessions lasted 137 days! Abbey Road, on the opposite," \
                     "was recorded in one 12-hour session -- even faster than Please Please Me! "
    slot_values["let_it_be"] = "Did you know that Abbey Road was created and issued after the recording of the Beatles' last released album took place?"
    response = node.response
    utt_list = nltk.sent_tokenize(response)
    resp_list = []
    all_slots = []
    spec_list = []
    resp_1 = []

    for utt in utt_list:
        utt_slots = re.findall(r"{(.*?)}", utt)
        if len(utt_slots) == 0:
            spec_list.append(utt_list.index(utt))
        for utt in utt_slots:
            all_slots.append(utt)

    if counter == 0:
        slot_value = slot_values.get(all_slots[0], "")
        slot_repl = "{" + all_slots[0] + "}"
        utt = all_slots[0].replace(slot_repl, slot_value)
        resp_1.append(utt)

    if len(all_slots) != 1:
        slot_value = slot_values.get(all_slots[1], "")
        slot_repl = "{" + all_slots[1] + "}"
        utt = all_slots[0].replace(slot_repl, slot_value)
        resp_1.append(utt)

    c = 0
    for i in range(len(utt_list)):
        if i in spec_list:
            resp_list.append(utt_list[i])
        else:
            resp_list.append(resp_1[c])
            c += 1

    node.response = " ".join(resp_list)
    return node_label, node


def extract_song_id(ctx: Context, actor: Actor, *args, **kwargs):
    songs = ["Hey Jude", "Don't Let Me Down", "We Can Work it Out", "Come Together",
             "Yellow Submarine", "Revolution", "Imagine", "Something", "Hello, Goodbye",
             "A Day In The Life", "Help!", "Penny Lane"]

    songs_ids = {"Hey Jude": "826kt29479qp27", "Don't Let Me Down": "hvnck9pvgnpft4",
                 "We Can Work it Out": "s1mfzw528vt05m", "Come Together": "qrg1tn7dpx2066",
                 "Yellow Submarine": "bsqcc0bkbkxb75", "Revolution": "grmx7c4g9rb412",
                 "Imagine": "rh8bfh6m7fr13g", "Something": "74v09tbmqmbf9z", "Hello, Goodbye": "87krd594czgd2d",
                 "A Day In The Life": "b8ptdvbm1rzccs", "Help!": "zk3dvf2qt7sr0p", "Penny Lane": "zhw7593t9mb9gn"}


    songs_re = "|".join(songs)
    vars = ctx.shared_memory.get("vars", {})
    user_uttr = state_utils.get_last_human_utterance(vars)
    extracted_song = re.findall(songs_re, user_uttr.get("text", ""), re.IGNORECASE)
    if extracted_song:
        for k in songs_ids.keys():
            if extracted_song[0].lower() == k.lower():
                id = songs_ids[k]

    return id




flows = {
    "beatles": {
        GLOBAL_TRANSITIONS: {("beatles", "beatles_q", priorities.high): "beatles"},
        GRAPH: {
            "start": {RESPONSE: "", TRANSITIONS: {("beatles", "beatles_q", priorities.high): "beatles"}},
            "beatles_q": {
                RESPONSE: "Do you like the Beatles?",
                PROCESSING: set_confidence_and_continue_flag(1.0, common_constants.MUST_CONTINUE),
                TRANSITIONS: {
                    ("beatles_fact", "name"): intents.yes_intent,
                    forward(): intents.always_true
                }
            },
            "instruments_q": {
                RESPONSE: "Are you interested in musical instruments?",
                TRANSITIONS: {
                    ("instruments", "play_q"): intents.yes_intent,
                    ("photos", "photos_q"): intents.always_true
                }
            }
        },
    },
    "beatles_fact": {
        GRAPH: {
            "name": {
                RESPONSE: "Beatles... Sound like a wordplay, doesn’t it? Beetles making the beat. That’s how they meant it",
                TRANSITIONS: {
                    ("album", "what_album"): intents.always_true
                }
            }
        },
    },
    "album": {
        GRAPH: {
            "what_album": {
                RESPONSE: "What's your favorite Beatles album?",
                TRANSITIONS: {
                    ("album", "please_please_me"): enter_album(album_name="Please Please Me"),
                    ("album", "with_the_beatles"): enter_album(album_name="With The Beatles"),
                    ("album", "a_hard_days_night_wrong"): enter_album(album_name="A Hard Day's Night"),
                    ("album", "beatles_for_sale"): enter_album(album_name="Beatles For Sale"),
                    ("album", "help"): enter_album(album_name="Help!"),
                    ("album", "rubber_soul"): enter_album(album_name="Rubber Soul"),
                    ("album", "revolver"): enter_album(album_name="revolver"),
                    ("album", "yellow_submarine"): enter_album(album_name="Yellow Submarine"),
                    ("album", "sgt_peppers"): enter_album(album_name="Sgt. Pepper's Lonely Hearts Club Band"),
                    ("album", "white_album"): enter_album(album_name="White Album"),
                    ("album", "abbey_road"): enter_album(album_name="Abbey Road"),
                    ("album", "let_it_be"): enter_album(album_name="Let It Be"),
                    ("album", "please_please_me"): intents.always_true
                }
            },
            "who_beatle": {
                RESPONSE: "By the way, who is your favorite Beatle?",
                TRANSITIONS: {
                    ("people", "fact_lennon"): has_lennon,
                    ("people", "fact_mccartney"): has_mccartney,
                    ("people", "fact_starr"): has_starr,
                    ("people", "fact_harrison"): has_harrison,
                    ("beatles", "instruments_q"): intents.always_true
                }
            },
            "please_please_me": {
                RESPONSE: "{first_album} Please Please Me is the first studio  album by the Beatles!"
                          "The album was recorded within 13 hours and the studio cost 400£. "
                          "The album hit the top of the British chart and stayed there for 30 weeks just to be replaced "
                          "by 'With the Beatles'. Quite unexpected for a debut, right?",
                PROCESSING: [slot_filling_albums,],
                TRANSITIONS: {
                    ("song", "song_q"): move_on,
                    ("album", "with_the_beatles"): not_visited_album
                },
                MISC: {
                    "command": "goto",
                    "objectId": "1vqwhwcpmh4t5k"
                }
            },
            "with_the_beatles": {
                RESPONSE: "{first_album}"
                          "'With the Beatles' was recorded in only 7 non-consecutive days, but overall its recording "
                          "took almost three months. Between the recording sessions the band was busy with radio, "
                          "TV and live performances. Do you remember the title of the Beatles' third studio album?",
                PROCESSING: [slot_filling_albums,],
                TRANSITIONS: {
                    ("song", "song_q"): move_on,
                    ("album", "a_hard_days_night_corr"): has_correct_answer,
                    ("album", "a_hard_days_night_wrong"): has_album
                },
                MISC: {
                    "command": "goto",
                    "objectId": "80nrsg1xgqk8ch"
                }
            },
            "a_hard_days_night_corr": {
                RESPONSE: "{first_album}"
                          "{a_hard_days_night_corr} "
                          "It was the band's third album, the first one to consist entirely of "
                          "the Beatles' original song and the only one to consist solely of songs written by Lennon-McCartney. "
                          "John Lennon later spoke of this album as typical for the Beatles' early period, "
                          "contrasting it to the later recordings: 'The early stuff – the Hard Day’s Night period, "
                          "I call it – was the seхual equivalent of the beginning hysteria of a relationship. "
                          "And the Sgt Pepper–Abbey Road period was the mature part of the relationship'.",
                PROCESSING: [slot_filling_albums,],
                TRANSITIONS: {
                    ("song", "song_q"): move_on,
                    ("album", "beatles_for_sale"): not_visited_album
                },
                MISC: {
                    "command": "goto",
                    "objectId": "2mm0prqv0rq7dh"
                }
            },
            "a_hard_days_night_wrong": {
                RESPONSE: "{first_album}"
                          "{a_hard_days_night_wrong} "
                          "It was the band's third album, the first one to consist entirely of "
                          "the Beatles' original song and the only one to consist solely of songs written by Lennon-McCartney. "
                          "John Lennon later spoke of this album as typical for the Beatles' early period, "
                          "contrasting it to the later recordings: 'The early stuff – the Hard Day’s Night period, "
                          "I call it – was the seхual equivalent of the beginning hysteria of a relationship. "
                          "And the Sgt Pepper–Abbey Road period was the mature part of the relationship'.",
                PROCESSING: [slot_filling_albums,],
                TRANSITIONS: {
                    ("song", "song_q"): move_on,
                    ("album", "beatles_for_sale"): not_visited_album
                },
                MISC: {
                    "command": "goto",
                    "objectId": "2mm0prqv0rq7dh"
                }
            },
            "beatles_for_sale": {
                RESPONSE: "{first_album}"
                          "Paul McCartney later said about the group's fourth album: 'Recording Beatles For Sale didn’t take long. "
                          "Basically it was our stage show, with some new songs.'. Even though today's "
                          "critics and listeners mostly agree with George Martin that 'the Beatles were rather war-weary during Beatles for Sale', "
                          "the album came out on the peak of Beatlemania and was a true hit: it stayed on top of the charts for 7 weeks.",
                PROCESSING: [slot_filling_albums,],
                TRANSITIONS: {
                    ("song", "song_q"): move_on,
                    ("album", "help"): not_visited_album
                },
                MISC: {
                    "command": "goto",
                    "objectId": "w2gnmmg1f34rkh"
                }
            },
            "help": {
                RESPONSE: "{first_album}"
                          "Just like A Hard Day's Night, one side of Help! consisted the soundtrack songs for the movie. "
                          "The other side included several famous songs, such as Yesterday, officially the most "
                          "covered song in the history of music. John Lennon later said that the title song "
                          "really was a cry for help: 'I was fat and depressed and I was crying out for 'Help'.'",
                PROCESSING: [slot_filling_albums,],
                TRANSITIONS: {
                    ("song", "song_q"): move_on,
                    ("album", "rubber_soul"): not_visited_album
                },
                MISC: {
                    "command": "goto",
                    "objectId": "xg3xm6mhb81m6c"
                }
            },
            "rubber_soul": {
                RESPONSE: "{first_album}"
                          "{rubber_soul} As John Lennon said, "
                          "'Finally we took over the studio. In the early days, we had to take what we were given, "
                          "we didn't know how you could get more bass. We were learning the technique on Rubber Soul. "
                          "We took over the cover and everything.'",
                PROCESSING: [slot_filling_albums,],
                TRANSITIONS: {
                    ("song", "song_q"): move_on,
                    ("album", "sgt_peppers"): not_visited_album
                },
                MISC: {
                    "command": "goto",
                    "objectId": "9wqs15r56psr2q"
                }
            },
            "revolver": {
                RESPONSE: "{first_album}"
                          "The Beatles second-best-selling album, Revolver, "
                          "was so technically complex that the band have never performed any of the songs from it live! "
                          "By the way, Revolver is Pope Benedict XVI's favourite album of all times. "
                          "One of the songs from it, Yellow Submarine, became an inspiration for an animated film! "
                          "Have you seen it?",
                TRANSITIONS: {
                    ("song", "song_q"): move_on,
                    ("album", "yellow_submarine"): intents.yes_intent,
                    ("song", "yellow_submarine"): intents.no_intent
                },
                MISC: {
                    "command": "goto",
                    "objectId": "86npm1z4m5mftr"
                }
            },
            "yellow_submarine": {
                RESPONSE: "{first_album} {yellow_submarine} One side of the album contains Beatles' song, "
                          "while the other one consists of symphonic film score composed by George Martin, "
                          "the Beatles' producer and the so-called fifth Beatle. Have you ever heard of this man?",
                PROCESSING: [slot_filling_albums, ],
                TRANSITIONS: {
                    ("song", "song_q"): move_on,
                    ("album", "sgt_peppers"): not_visited_album
                },
                MISC: {
                    "command": "goto",
                    "objectId": "ht5p6z4rs7zf65"
                }
            },
            "sgt_peppers": {
                RESPONSE: "{first_album} "
                          "Called 'a decisive moment in the history of Western civilisation', "
                          "'the most important and influential rock and roll album ever recorded' and "
                          "'a historic departure in the progress of music', Sgt. Pepper's Lonely Hearts Club Band is the Beatles' best-selling album "
                          "of all times. More than 32 million copies of Sgt. Pepper's Lonely Hearts Club Band were sold all over the world! "
                          "A stunning number, isn't it?",
                PROCESSING: [slot_filling_albums, ],
                TRANSITIONS: {
                    ("song", "song_q"): move_on,
                    ("album", "white_album"): not_visited_album
                },
                MISC: {
                    "command": "goto",
                    "objectId": "n0kgrcdqqqfpqq"
                }
            },
            "white_album": {
                RESPONSE: "{first_album} Unlike the earlier period, the idea of the band's The Beatles, or the White Album, "
                          "was almost entirely conceived far from London. The group went to an ashram in Rishikesh, India, "
                          "for a meditation course, where they only had an acoustic guitar available! Even though the album "
                          "was not critically acclaimed, Lennon said: 'I think it’s the best music we’ve ever made', "
                          "however adding: 'But as a Beatles thing, as a whole, it just doesn’t work'."
                          "What do you think about this album?",
                PROCESSING: [slot_filling_albums, ],
                TRANSITIONS: {
                    ("song", "song_q"): move_on,
                    ("album", "abbey_road"): not_visited_album
                },
                MISC: {
                    "command": "goto",
                    "objectId": "h8fxrqh4611dg3"
                }
            },
            "abbey_road": {
                RESPONSE: "{first_album} {abbey_road} "
                          "Abbey Road's working title was Everest, but they say that the band didn't like the idea of "
                          "going to Mount Everest to do a photoshoot for the cover. So they invented another title "
                          "- Abbey Road, after the street where most of the band's material was recorded. By the way, "
                          "do you remember what the album's cover looks like?",
                PROCESSING: [slot_filling_albums, ],
                TRANSITIONS: {
                    ("song", "song_q"): move_on,
                    ("album", "abbey_road_cover"): intents.no_intent,
                    ("album", "let_it_be"): intents.always_true
                },
                MISC: {
                    "command": "goto",
                    "objectId": "665x7hc4s22wpv"
                }
            },
            "abbey_road_cover": {
                RESPONSE: "Then let me show it to you! The photoshoot was Paul McCartney's idea. It happened right outside the bands' "
                          "recording studio and took less than half an hour.",
                TRANSITIONS: {
                    ("song", "song_q"): move_on,
                    ("album", "let_it_be"): not_visited_album
                },
                MISC: {
                    "command": "goto",
                    "objectId": "z3nfvv0r06v3kx"
                }
            },
            "let_it_be": {
                RESPONSE: "{first_album} {let_it_be} "
                          "Originally, the band's last album was called Get Back, but later its name was changed to Let It Be. "
                          "The band wanted to record it live in front of an audience in an exotic location, "
                          "but at last the recording took place in a studio. The album spent more than a year unreleased "
                          "as the relations between the Beatles had become so tense that none of them wanted to sort the songs out.",
                PROCESSING: [slot_filling_albums, ],
                TRANSITIONS: {
                    ("song", "song_q"): move_on,
                    ("album", "please_please_me"): not_visited_album
                },
                MISC: {
                    "command": "goto",
                    "objectId": "4n02cf8h4qx00c"
                }
            }
        },
    },
    "photos": {
        GRAPH: {
            "photos_q": {
                RESPONSE: "Would you like to see some pictures of The Beatles?",
                TRANSITIONS: {
                    ("photos", "abbey_road"): intents.yes_intent
                }
            },
            "abbey_road": {
                RESPONSE: """Here! It's the only original Beatles album cover to show neither the artist name nor"""
                          """the album title. Do you remember the name of this album?""",
                TRANSITIONS: {
                    ("photos", "fact_ar"): has_correct_answer,
                    ("photos", "info_ar"): intents.always_true
                },
                MISC: {
                    "command": "goto",
                    "objectId": "b9d08nbdvh8vsb"
                }
            },
            "fact_ar": {
                RESPONSE: """Yes, it's Abbey Road!! Did you know that after the album was released, the number plate """
                          """"(LMW 281F) was repeatedly stolen from the white Volkswagen Beetle from the picture? Poor owner"""
                          """of the car...""",
                TRANSITIONS: {
                    ("photos", "yesterday&today"): intents.always_true
                }
            },
            "info_ar": {
                RESPONSE: """It's Abbey Road! Photographer was given only 10 minutes to take the photo while he stood """
                          """on a step-ladder and a policeman held up traffic behind the camera. He took 6 photographs and """
                          """McCartney chose this one for the cover""",
                TRANSITIONS: {
                    ("photos", "yesterday&today"): intents.always_true
                }
            },
            "yesterday&today": {
                RESPONSE: """This photo is from Whitaker photo session, where he assembled different scary props such"""
                          """as doll parts and trays of meat. One of the photos was used for the cover of Yesterday """
                          """and Today album. We have some more photos of The Beatles, so be sure to check them out 🙂 """,
                MISC: {
                    "command": "goto",
                    "objectId": "pv2qgzk51vmgq6"
                }
            }
        },
    },
    "song": {
        GRAPH: {
            "song_q": {
                RESPONSE: "All right, let's finish the albums here. What's your favorite Beatles song?",
                TRANSITIONS: {
                    ("song", "fav_song"): has_songs,
                    ("song", "why_song"): intents.always_true
                }
            },
            "fav_song": {
                RESPONSE: "Oh, have you seen the music video for this song?",
                PROCESSING: [extract_song_id,],
                TRANSITIONS: {
                    ("album", "who_beatle"): intents.yes_intent,
                    ("song", "watch_video"): intents.always_true
                }
            },
            "watch_video": {
                RESPONSE: "Do you want to watch it?",
                TRANSITIONS: {
                    ("song", "show_video"): intents.yes_intent,
                    ("album", "who_beatle"): intents.always_true
                }
            },
            "show_video": {
                RESPONSE: "Great! You can watch it 🙂 "
                          "Just text me when you're done",
                TRANSITIONS: {
                    ("album", "who_beatle"): intents.always_true
                },
                MISC: {
                    "command": "goto",
                    "objectId": "{video}"
                }
            },
            "why_song": {
                RESPONSE: "Why do you like this song?",
                TRANSITIONS: {
                    ("album", "who_beatle"): intents.always_true
                }
            },
            "yellow_submarine": {
                RESPONSE: "Then let's watch a short video and after that you can watch the entire movie if you want! "
                          "Just text me when you're done.",
                TRANSITIONS: {
                    ("album", "yellow_submarine"): intents.always_true
                },
                MISC: {
                    "command": "goto",
                    "objectId": "86hcq66wcfgszf"
                }
            }
        },
    },
    "people": {
        GRAPH: {
            "name": {
                RESPONSE: "Yeah, I like {beatles_member} too! Do you want to take a look at his biography?",
                PROCESSING: [extract_members,
                             custom_functions.slot_filling, ],
                TRANSITIONS: {
                    ("people", "bio"): intents.yes_intent,
                    ("beatles", "instruments_q"): intents.always_true
                }
            },
            "bio": {
                RESPONSE: "Here! Text me when you're done :)",
                TRANSITIONS: {
                    ("beatles", "instruments_q"): intents.always_true
                },
                MISC: {
                    "command": "goto",
                    "objectId": "{beatles_member}"
                }
            },
            "fact_lennon": {
                RESPONSE: "Yeah, I like {beatles_member} too! By the way, did you know that John Lennon’s father"
                          " was absent for much of his early life but showed up when his son became famous?"
                          " Sounds kind of sad... Do you want to take a look at his biography?",
                PROCESSING: [extract_members,
                             custom_functions.slot_filling, ],
                TRANSITIONS: {
                    ("people", "bio"): intents.yes_intent,
                    ("beatles", "instruments_q"): intents.always_true
                }
            },
            "fact_mccartney": {
                RESPONSE: "Yeah, I like {beatles_member} too! By the way, did you know that Paul McCartney played"
                          " to what's believed to be the largest paid audience in recorded history? In 1989,"
                          " he played a solo concert to a crowd of 350,000-plus in Brazil. That's amazing!"
                          "Do you want to take a look at his biography?",
                PROCESSING: [extract_members,
                             custom_functions.slot_filling, ],
                TRANSITIONS: {
                    ("people", "bio"): intents.yes_intent,
                    ("beatles", "instruments_q"): intents.always_true
                }
            },
            "fact_harrison": {
                RESPONSE: "Yeah, I like {beatles_member} too! By the way, did you know that"
                          " the song ‘CRACKERBOX PALACE’ is about his mansion?  Modest as he was - he did live"
                          " in a 120 room mansion on a 66 acre estate. Do you want to take a look at his biography?",
                PROCESSING: [extract_members,
                             custom_functions.slot_filling, ],
                TRANSITIONS: {
                    ("people", "bio"): intents.yes_intent,
                    ("beatles", "instruments_q"): intents.always_true
                }
            },
            "fact_starr": {
                RESPONSE: "Yeah, I like {beatles_member} too! By the way, did you know that due to his allergy"
                          " he has never had pizza, curry, or onions? That didn’t stop him from doing a pizza"
                          " commercial in 1995, though. Do you want to take a look at his biography?",
                PROCESSING: [extract_members,
                             custom_functions.slot_filling, ],
                TRANSITIONS: {
                    ("people", "bio"): intents.yes_intent,
                    ("beatles", "instruments_q"): intents.always_true
                }
            }
        },
    },
    "instruments": {
        GRAPH: {
            "guitar": {
                RESPONSE: "Cool! I can show you Paul McCartney's guitar!"
            },
            "play_q": {
                RESPONSE: "And do you play any instrument?",
                TRANSITIONS: {
                    ("instruments", "guitar_paul_1"): intents.yes_intent,
                    ("instruments", "guitar_paul_1_2"): intents.always_true
                }
            },
            "guitar_paul_1": {
                RESPONSE: "Cool! We have a lot of {guitar}s here. "
                          "Let's begin with a story about Paul McCartney's first {guitar}. "
                          "I have a funny story about {trumpet}s for you. "
                          "If you like {drums}, you must like Ringo Starr! We will see his {drums} later, "
                          "let's begin with the guitars. "
                          "In 1956, McCartney's father gave him a trumpet for his birthday. "
                          """But, as Paul said later, "you couldn't sing with a trumpet stuck in your mouth", """
                          "so he traded it for Zenith Model 17 acoustic. Let's have a look at it. "  
                          "At first, Paul couldn't figure out how to play it, but then he realized that " 
                          "he had to hold the guitar differently as he was left-handed. Isn't it beautiful?",
                PROCESSING: [extract_inst,
                             custom_functions.slot_filling, ],
                TRANSITIONS: {
                    ("instruments", "guitar_paul_2"): intents.always_true
                },
                MISC: {
                    "command": "goto",
                    "objectId": "f47z2rzm0tt4b8"
                }
            },
            "guitar_paul_1_2": {
                RESPONSE: "I can show you Paul McCartney's guitar!"
                          "In 1956, McCartney's father gave him a trumpet for his birthday. "
                          """But, as Paul said later, "you couldn't sing with a trumpet stuck in your mouth", """
                          "so he traded it for Zenith Model 17 acoustic. Let's have a look at it. "
                          "At first, Paul couldn't figure out how to play it, but then he realized that "
                          "he had to hold the guitar differently as he was left-handed. Isn't it beautiful?",
                TRANSITIONS: {
                    ("instruments", "guitar_paul_2"): intents.always_true
                },
                MISC: {
                    "command": "goto",
                    "objectId": "f47z2rzm0tt4b8"
                }
            },
            "guitar_paul_2": {
                RESPONSE: " And here is Paul's Hofner 500/1 bass. "
                          """He went with this Hofner from "I Want to Hold Your Hand" through "Let It Be" and beyond. """
                          "Do you want to take a look at one of John Lennon's guitars?",
                TRANSITIONS: {
                    ("instruments", "guitar_lennon"): intents.yes_intent,
                    ("photos", "photos_q"): intents.always_true
                },
                MISC: {
                    "command": "goto",
                    "objectId": "r369t7g5cw3x0h"
                }
            },
            "guitar_lennon": {
                RESPONSE: """Look! It's Lennon's Rickenbacker 325! He had four models of this guitar. Do you like it?""",
                TRANSITIONS: {
                    ("instruments", "drum_kit"): intents.always_true
                },
                MISC: {
                    "command": "goto",
                    "objectId": "07ptwckzth85qz"
                }
            },
            "drum_kit": {
                RESPONSE: "Well, now that you've seen the guitars it's time to look at Ringo Starr's "
                          "drum kit. During his time in The Beatles, he played six different drum kits, " 
                          "five of which were from Ludwig.",
                TRANSITIONS: {
                    ("photos", "photos_q"): intents.always_true
                },
                MISC: {
                    "command": "goto",
                    "objectId": "vx6bwczc94mtpq"
                }
            }
        }
    },
}
