import common.universal_templates as templates
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
    members= ["John Lennon", "Ringo Starr", "Paul McCartney", "George Harrison"]

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
    "photos": {
        GRAPH: {
            "photos_q": {
                RESPONSE: "Would you like to see some pictures of The Beatles?",
                TRANSITIONS: {
                    ("photos", "abbey_road"): intents.yes_intent
                }
            },
            "abbey_road": {
                RESPONSE: """(go to abbey road cover photo) Do you reсognize this photo?"""
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
                    ("album", "who_beatle"): intents.always_true
                }
            },
            "who_beatle": {
                RESPONSE: "And who is your favorite Beatle?",
                TRANSITIONS: {
                    ("people", "name"): has_members,
                    ("beatles", "instruments_q"): intents.always_true
                }
            },
            "the_album": {
                RESPONSE: "Cool! Let's have a look at it. go to {beatles_album} & give fun fact about {beatles_album} What is your favourite song from {beatles_album}?",
                PROCESSING: [custom_functions.entities(user_fav_album="wiki:Q7165642"),
                            custom_functions.slot_filling,],
                TRANSITIONS: {
                    ("album", "who_beatle"): intents.always_true
                }
            }
        },
    },
    "song": {
        GRAPH: {
            "song_q": {
                RESPONSE: "Cool! Let's have a look at it. %TELL FUN FACT% What is your favourite song from {beatles_album}?",
                # RESPONSE: ["Cool! Let's have a look at it. %TELL FUN FACT% What is your favourite song from {beatles_album}?", "roomful:goto_album:{beatles_album}"]
                PROCESSING: [
                    extract_albums,
                    custom_functions.slot_filling,
                    # beatles_functions.add_album_wikidata_id
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
                RESPONSE: "Great! You can watch it :) (go to the video). Just text me when you're done",
                TRANSITIONS: {
                    ("album", "who_beatle"): intents.always_true
                }
            },
            "why_song": {
                RESPONSE: "Why do you like this song?",
                TRANSITIONS: {
                    ("album", "who_beatle"): intents.always_true
                }
            }
        },
    },
    "people": {
        GRAPH: {
            "name": {
                RESPONSE: "Yeah, I like {beatles_member} too! Do you want to take a look at his biography?",
                PROCESSING: [extract_members,
                            custom_functions.slot_filling,],
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
                RESPONSE: """Cool! We have a lot of guitars here. I can show you Paul McCartney's first guitar! (go to guitar)
                          In 1956, McCartney's father gave him a trumpet for his birthday. But Paul understood that
                           "you couldn't sing with a trumpet stuck in your mouth", so he traded it for Zenith Model 17 acoustic.
                            At first, he couldn't figure out how to play it, but then he realized that due to the fact that he was left-handed, 
                            he had to hold the guitar differently. Isn't it beautiful?""",
                TRANSITIONS: {
                    ("instruments", "guitar_paul_2"): intents.yes_intent
                }
            },
            "guitar_paul_1_2": {
                RESPONSE: """I can show you Paul McCartney's guitar! (go to guitar) 
                 In 1956, McCartney's father gave him a trumpet for his birthday. 
                 But Paul understood, that "you couldn't sing with a trumpet stuck in your mouth", 
                 so he traded it for Zenith Model 17 acoustic. At first, he couldn't figure out how to play it,
                  but then he realized that due to the fact that he was left-handed, he had to hold the guitar 
                  differently. Isn't it beautiful?""",
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
                RESPONSE: """go to drums) Well, now that you have seen the guitars 
                it's time to look at the drum kit that Ringo Starr played. 
                During his time in The Beatles, he played six different drum kits, 
                five of which were from Ludwig."""
            }
        }
    },
}
