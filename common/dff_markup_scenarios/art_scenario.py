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


def has_members(ctx: Context, actor: Actor, *args, **kwargs):
    flag = False
    members = ["John Lennon", "Ringo Starr", "Paul McCartney", "George Harrison"]

    members_re = "|".join(members)
    vars = ctx.shared_memory.get("vars", {})
    user_uttr = state_utils.get_last_human_utterance(vars)
    extracted_member = re.findall(members_re, user_uttr.get("text", ""), re.IGNORECASE)
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


# visited_albums = []
#
#
# def not_visited_album(ctx: Context, actor: Actor, *args, **kwargs):
#     all_albums = ["Please Please Me", "With the Beatles", "Introducing... The Beatles", "Meet the Beatles!",
#                   "Twist and Shout", "The Beatles' Second Album", "The Beatles' Long Tall Sally", "A Hard Day's Night",
#                   "Something New", "Help!", "Sgt. Pepper's Lonely Hearts Club Band", "White Album", "The Beatles Beat",
#                   "Another Beatles Christmas Record", "Beatles '65", "Beatles VI", "Five Nights In A Judo Arena",
#                   "The Beatles at the Hollywood Bowl", "Live! at the Star-Club in Hamburg, German; 1962",
#                   "The Black Album", "20 Exitos De Oro", "A Doll's House", "The Complete Silver Beatles",
#                   "Rock 'n' Roll Music Vol. 1", "Yellow Submarine", "Let It Be", "Beatles for Sale",
#                   "Revolver", "Abbey Road", "Rubber Soul"]
#     flag = False
#     all_albums_re = "|".join(all_albums)
#     vars = ctx.shared_memory.get("vars", {})
#     user_uttr = state_utils.get_last_human_utterance(vars)
#     extracted_album = re.findall(all_albums_re, user_uttr.get("text", ""), re.IGNORECASE)


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
                    ("song", "song_q"): has_album,
                    ("album", "sgt_peppers"): intents.always_true
                }
            },
            "who_beatle": {
                RESPONSE: "All right, let's finish the albums here. Who is your favorite Beatle?",
                TRANSITIONS: {
                    ("people", "name"): has_members,
                    ("beatles", "instruments_q"): intents.always_true
                }
            },
            "sgt_peppers": {
                RESPONSE: "Let's begin our trip here. I will show you some albums first. If you get tired, just text me 'MOVE ON'"
                          "(go to Sgt. Pepper's Lonely Hearts Club Band)"
                          "Have you known that Sgt. Pepper's Lonely Hearts Club Band is the Beatles' best-selling album"
                          "of all times? More than 32 million copies of Sgt. Pepper's Lonely Hearts Club Band were sold "
                          "all over the world! 5 millions more copies than the second-best-selling one, Revolver. "
                          "A stunning number, isn't it?",
                TRANSITIONS: {
                    ("album", "who_beatle"): move_on,
                    ("album", "revolver"): intents.always_true
                }
            },
            "revolver": {
                RESPONSE: "(go to Revolver) The Beatles second-best-selling album, Revolver, "
                          "was so technically complex that the band have never performed any of the songs from it live! "
                          "By the way, Revolver is Pope Benedict XVI's favourite album of all times. "
                          "One of the songs from it, Yellow Submarine, became an inspiration for an animated film! "
                          "Have you seen it?",
                TRANSITIONS: {
                    ("album", "who_beatle"): move_on,
                    ("album", "yellow_submarine"): intents.yes_intent,
                    ("song", "yellow_submarine"): intents.no_intent
                }
            },
            "yellow_submarine": {
                RESPONSE: "Then let's take a look at the album. One side of the album contains Beatles' song, "
                          "while the other one consists of symphonic film score composed by George Martin, "
                          "the Beatles' producer and the so-called fifth beatle. Have you ever heard of this man?",
                TRANSITIONS: {
                    ("album", "who_beatle"): move_on,
                    ("album", "please_please_me"): intents.always_true
                }
            },
            "please_please_me": {
                RESPONSE: "George Martin was together with the band since their first single, Love Me Do. "
                          "There are three versions of the song, the final of which is available on Please Please Me, "
                          "the Beatles' debut album (go to Please Please Me). "
                          "This album was recorded within 13 hours and the studio cost 400£. "
                          "The album hit the top of the British chart and stayed there for 30 weeks just to be replaced "
                          "by 'With the Beatles'. Quite unexpected for a debut, right?",
                TRANSITIONS: {
                    ("album", "who_beatle"): move_on,
                    ("album", "with_the_beatles"): intents.always_true
                }
            },
            "with_the_beatles": {
                RESPONSE: "(go to With the Beatles album) "
                          "'With the Beatles' was recorded in only 7 non-consecutive days, but overall its recording "
                          "took almost three months. Between the recording sessions the band was busy with radio, "
                          "TV and live performances. Do you remember the title of the Beatles' third studio album?",
                TRANSITIONS: {
                    ("album", "who_beatle"): move_on,
                    ("album", "a_hard_days_night_corr"): has_correct_answer,
                    ("album", "a_hard_days_night_wrong"): intents.always_true
                }
            },
            "a_hard_days_night_corr": {
                RESPONSE: "(go to A Hard Day's Night) "
                          "And you're right, A Hard Day's Night it was! "
                          "It was the band's third album, the first one to consist entirely of "
                          "the Beatles' original song and the only one to consist solely of songs written by Lennon-McCartney. "
                          "John Lennon later spoke of this album as typical for the Beatles' early period, "
                          "contrasting it to the later recordings: 'The early stuff – the Hard Day’s Night period, "
                          "I call it – was the seхual equivalent of the beginning hysteria of a relationship. "
                          "And the Sgt Pepper–Abbey Road period was the mature part of the relationship'.",
                TRANSITIONS: {
                    ("album", "who_beatle"): intents.always_true
                }
            },
            "a_hard_days_night_wrong": {
                RESPONSE: "(go to A Hard Day's Night) "
                          "And you're right, A Hard Day's Night it was! "
                          "It was the band's third album, the first one to consist entirely of "
                          "the Beatles' original song and the only one to consist solely of songs written by Lennon-McCartney. "
                          "John Lennon later spoke of this album as typical for the Beatles' early period, "
                          "contrasting it to the later recordings: 'The early stuff – the Hard Day’s Night period, "
                          "I call it – was the seхual equivalent of the beginning hysteria of a relationship. "
                          "And the Sgt Pepper–Abbey Road period was the mature part of the relationship'.",
                TRANSITIONS: {
                    ("album", "who_beatle"): intents.always_true
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
                RESPONSE: """Here! It's the only original Beatles album cover to show neither the artist name nor the album title. Do you remember the name of this album?""",
                TRANSITIONS: {
                    ("photos", "fact_ar"): has_correct_answer,
                    ("photos", "info_ar"): intents.always_true
                }
            },
            "fact_ar": {
                RESPONSE: """Yes, it's Abbey Road!! Did you know that after the album was released, the number plate (LMW 281F) was repeatedly stolen from the white Volkswagen Beetle from the picture? Poor owner of the car...""",
                TRANSITIONS: {
                    ("photos", "yesterday&today"): intents.always_true
                }
            },
            "info_ar": {
                RESPONSE: """It's Abbey Road! Photographer was given only 10 minutes to take the photo while he stood on a step-ladder and a policeman held up traffic behind the camera. He took 6 photographs and McCartney chose this one for the cover""",
                TRANSITIONS: {
                    ("photos", "yesterday&today"): intents.always_true
                }
            },
            "yesterday&today": {
                RESPONSE: """This photo is from Whitaker photo session, where he assembled different scary props such as doll parts and trays of meat. One of the photos was used for the cover of Yesterday and Today album. We have some more photos of The Beatles, so be sure to check them out 🙂 """
            }
        },
    },
    "song": {
        GRAPH: {
            "song_q": {
                RESPONSE: "Cool! Let's have a look at it. (go to album) Have you known that {Sgt. Pepper's Lonely Hearts Club Band}"
                          "is the Beatles' best-selling album of all times? More than 32 million copies of {Sgt. Pepper's Lonely Hearts Club Band}"
                          "were sold all over the world!"
                          "What is your favourite song from {beatles_album}?",
                PROCESSING: [
                    extract_albums,
                    custom_functions.slot_filling,
                ],
                TRANSITIONS: {
                    ("song", "fav_song"): has_songs,
                    ("song", "why_song"): intents.always_true
                }
            },
            "fav_song": {
                RESPONSE: "Oh, have you seen the music video for this song?",
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
                RESPONSE: "Great! You can watch it 🙂 (go to the video). Just text me when you're done",
                TRANSITIONS: {
                    ("album", "who_beatle"): intents.always_true
                }
            },
            "why_song": {
                RESPONSE: "Why do you like this song?",
                TRANSITIONS: {
                    ("album", "who_beatle"): intents.always_true
                }
            },
            "yellow_submarine": {
                RESPONSE: "(go to Yellow Submarine video)"
                          "Then let's watch a short video and after that you can watch the entire movie if you want! "
                          "Just text me when you're done.",
                TRANSITIONS: {
                    ("album", "yellow_submarine"): intents.always_true
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
                RESPONSE: "(go to biography) Here! Text me when you're done :)",
                TRANSITIONS: {
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
                RESPONSE: """Cool! We have a lot of {guitar}s here. 
                Let's begin with a story about Paul McCartney's first {guitar}.
                I have a funny story about {trumpet}s for you.
                If you like {drums}, you must like Ringo Starr! We will see his {drums} later,
                let's begin with the guitars.
                 In 1956, McCartney's father gave him a trumpet for his birthday. 
                 But, as Paul said later, "you couldn't sing with a trumpet stuck in your mouth", 
                 so he traded it for Zenith Model 17 acoustic. Let's have a look at it. (go to guitar)  
                 At first, Paul couldn't figure out how to play it, but then he realized that 
                 he had to hold the guitar differently as he was left-handed. Isn't it beautiful?""",
                PROCESSING: [extract_inst,
                             custom_functions.slot_filling, ],
                TRANSITIONS: {
                    ("instruments", "guitar_paul_2"): intents.yes_intent
                }
            },
            "guitar_paul_1_2": {
                RESPONSE: """I can show you Paul McCartney's guitar! (go to guitar) 
                 In 1956, McCartney's father gave him a trumpet for his birthday. 
                 But, as Paul said later, "you couldn't sing with a trumpet stuck in your mouth", 
                 so he traded it for Zenith Model 17 acoustic. Let's have a look at it. (go to guitar)  
                 At first, Paul couldn't figure out how to play it, but then he realized that 
                 he had to hold the guitar differently as he was left-handed.""",
                TRANSITIONS: {
                    ("instruments", "guitar_paul_2"): intents.yes_intent
                }
            },
            "guitar_paul_2": {
                RESPONSE: """(go to guitar) And here is Paul's Hofner 500/1 bass. 
                He went with this Hofner from "I Want to Hold Your Hand" through "Let It Be" and beyond.
                Do you want to take a look at one of John Lennon's guitars?""",
                TRANSITIONS: {
                    ("instruments", "guitar_lennon"): intents.yes_intent
                }
            },
            "guitar_lennon": {
                RESPONSE: """(go to guitar) Look! It's Lennon's Rickenbacker 325! He had four models of this guitar.
                 Do you like it?""",
                TRANSITIONS: {
                    ("instruments", "drum_kit"): intents.yes_intent
                }
            },
            "drum_kit": {
                RESPONSE: """(go to drums) Well, now that you've seen the guitars it's time to look at Ringo Starr's 
                drum kit. During his time in The Beatles, he played six different drum kits, 
                five of which were from Ludwig."""
            }
        }
    },
}
