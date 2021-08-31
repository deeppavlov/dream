import logging
import re

from dff.core.keywords import TRANSITIONS, GRAPH, RESPONSE, GLOBAL_TRANSITIONS, PROCESSING, MISC
from dff.core import Actor
import dff.conditions as cnd
import dff.transitions as trn

import common.dff.integration.condition as int_cnd
from . import condition as loc_cnd
from . import processing as loc_prs

logger = logging.getLogger(__name__)

# First of all, to create a dialog agent, we need to create a dialog script.
# Below, `flows` is the dialog script.
# A dialog script is a flow dictionary that can contain multiple flows .
# Flows are needed in order to divide a dialog into sub-dialogs and process them separately.
# For example, the separation can be tied to the topic of the dialog.
# In our example, there is one flow called greeting_flow.

# Inside each flow, we can describe a sub-dialog using keyword `GRAPH` from dff.core.keywords module.
# Here we can also use keyword `GLOBAL_TRANSITIONS`, which we have considered in other examples.

# `GRAPH` describes a sub-dialog using linked nodes, each node has the keywords `RESPONSE` and `TRANSITIONS`.

# `RESPONSE` - contains the response that the dialog agent will return when transitioning to this node.
# `TRANSITIONS` - describes transitions from the current node to other nodes.
# `TRANSITIONS` are described in pairs:
#      - the node to which the agent will perform the transition
#      - the condition under which to make the transition
flows = {
    "beatles": {
        GLOBAL_TRANSITIONS: {("beatles", "beatles_q"): cnd.regexp(r"\bbeatles\b", re.I)},
        GRAPH: {
            "start": {RESPONSE: ""},
            "beatles_q": {
                RESPONSE: "Do you like the Beatles?",
                # PROCESSING: set_confidence_and_continue_flag(1.0, common_constants.MUST_CONTINUE,
                # ),
                TRANSITIONS: {
                    ("beatles_fact", "name"): int_cnd.is_yes_vars,
                    trn.forward(): cnd.true,
                },
            },
            "instruments_q": {
                RESPONSE: "Are you interested in musical instruments?",
                TRANSITIONS: {
                    ("instruments", "play_q"): int_cnd.is_yes_vars,
                    ("photos", "photos_q"): cnd.true,
                },
            },
        },
    },
    "beatles_fact": {
        GRAPH: {
            "name": {
                RESPONSE: "Beatles... Sound like a wordplay, doesn’t it? Beetles making the beat. "
                "That’s how they meant it",
                TRANSITIONS: {("album", "what_album"): cnd.true},
            }
        },
    },
    "album": {
        GRAPH: {
            "what_album": {
                RESPONSE: "What's your favorite Beatles album?",
                TRANSITIONS: {
                    ("album", "please_please_me"): loc_cnd.has_album(album_name="Please Please Me"),
                    ("album", "with_the_beatles"): loc_cnd.has_album(album_name="With The Beatles"),
                    ("album", "a_hard_days_night_wrong"): loc_cnd.has_album(album_name="A Hard Day's Night"),
                    ("album", "beatles_for_sale"): loc_cnd.has_album(album_name="Beatles For Sale"),
                    ("album", "help"): loc_cnd.has_album(album_name="Help!"),
                    ("album", "rubber_soul"): loc_cnd.has_album(album_name="Rubber Soul"),
                    ("album", "revolver"): loc_cnd.has_album(album_name="revolver"),
                    ("album", "yellow_submarine"): loc_cnd.has_album(album_name="Yellow Submarine"),
                    ("album", "sgt_peppers"): loc_cnd.has_album(album_name="Sgt. Pepper's Lonely Hearts Club Band"),
                    ("album", "white_album"): loc_cnd.has_album(album_name="White Album"),
                    ("album", "abbey_road"): loc_cnd.has_album(album_name="Abbey Road"),
                    ("album", "let_it_be"): loc_cnd.has_album(album_name="Let It Be"),
                    ("album", "please_please_me", 0): cnd.true,
                },
            },
            "who_beatle": {
                RESPONSE: "By the way, who is your favorite Beatle?",
                TRANSITIONS: {
                    ("people", "fact_lennon"): loc_cnd.has_member(member_name="John Lennon"),
                    ("people", "fact_mccartney"): loc_cnd.has_member(member_name="Paul McCartney"),
                    ("people", "fact_starr"): loc_cnd.has_member(member_name="Ringo Starr"),
                    ("people", "fact_harrison"): loc_cnd.has_member(member_name="George Harrison"),
                    ("beatles", "instruments_q"): cnd.true,
                },
            },
            "please_please_me": {
                RESPONSE: "{first_album} Please Please Me is the first studio  album by the Beatles!"
                "The album was recorded within 13 hours and the studio cost 400£. "
                "The album hit the top of the British chart and stayed there for 30 weeks just to be replaced "
                "by 'With the Beatles'. Quite unexpected for a debut, right?",
                PROCESSING: [
                    loc_prs.increment_album_counter,
                    loc_prs.slot_filling_albums,
                    loc_prs.add_misc_to_response,
                ],
                TRANSITIONS: {
                    ("song", "song_q"): loc_cnd.move_on,
                    ("album", "with_the_beatles"): loc_cnd.not_visited_album,
                    ("song", "song_q", 0.1): cnd.true,
                },
                MISC: {"command": "goto", "objectId": "1vqwhwcpmh4t5k"},
            },
            "with_the_beatles": {
                RESPONSE: "{first_album}"
                "'With the Beatles' was recorded in only 7 non-consecutive days, but overall its recording "
                "took almost three months. Between the recording sessions the band was busy with radio, "
                "TV and live performances. Do you remember the title of the Beatles' third studio album?",
                PROCESSING: [
                    loc_prs.increment_album_counter,
                    loc_prs.slot_filling_albums,
                    loc_prs.add_misc_to_response,
                ],
                TRANSITIONS: {
                    ("song", "song_q"): loc_cnd.move_on,
                    ("album", "a_hard_days_night_corr"): loc_cnd.has_correct_answer,
                    ("album", "a_hard_days_night_wrong"): cnd.true,
                },
                MISC: {"command": "goto", "objectId": "80nrsg1xgqk8ch"},
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
                PROCESSING: [
                    loc_prs.increment_album_counter,
                    loc_prs.slot_filling_albums,
                    loc_prs.add_misc_to_response,
                ],
                TRANSITIONS: {
                    ("song", "song_q"): loc_cnd.move_on,
                    ("album", "beatles_for_sale"): loc_cnd.not_visited_album,
                    ("song", "song_q", 0.1): cnd.true,
                },
                MISC: {"command": "goto", "objectId": "2mm0prqv0rq7dh"},
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
                PROCESSING: [
                    loc_prs.increment_album_counter,
                    loc_prs.slot_filling_albums,
                    loc_prs.add_misc_to_response,
                ],
                TRANSITIONS: {
                    ("song", "song_q"): loc_cnd.move_on,
                    ("album", "beatles_for_sale"): loc_cnd.not_visited_album,
                    ("song", "song_q", 0.1): cnd.true,
                },
                MISC: {"command": "goto", "objectId": "2mm0prqv0rq7dh"},
            },
            "beatles_for_sale": {
                RESPONSE: "{first_album}"
                "Paul McCartney later said about the group's fourth album: "
                "'Recording Beatles For Sale didn’t take long. "
                "Basically it was our stage show, with some new songs.'. Even though today's "
                "critics and listeners mostly agree with George Martin that "
                "'the Beatles were rather war-weary during Beatles for Sale', "
                "the album came out on the peak of Beatlemania and was a true hit: "
                "it stayed on top of the charts for 7 weeks.",
                PROCESSING: [
                    loc_prs.increment_album_counter,
                    loc_prs.slot_filling_albums,
                    loc_prs.add_misc_to_response,
                ],
                TRANSITIONS: {
                    ("song", "song_q"): loc_cnd.move_on,
                    ("album", "help"): loc_cnd.not_visited_album,
                    ("song", "song_q", 0.1): cnd.true,
                },
                MISC: {"command": "goto", "objectId": "w2gnmmg1f34rkh"},
            },
            "help": {
                RESPONSE: "{first_album}"
                "Just like A Hard Day's Night, one side of Help! consisted the soundtrack songs for the movie. "
                "The other side included several famous songs, such as Yesterday, officially the most "
                "covered song in the history of music. John Lennon later said that the title song "
                "really was a cry for help: 'I was fat and depressed and I was crying out for 'Help'.'",
                PROCESSING: [
                    loc_prs.increment_album_counter,
                    loc_prs.slot_filling_albums,
                    loc_prs.add_misc_to_response,
                ],
                TRANSITIONS: {
                    ("song", "song_q"): loc_cnd.move_on,
                    ("album", "rubber_soul"): loc_cnd.not_visited_album,
                    ("song", "song_q", 0.1): cnd.true,
                },
                MISC: {"command": "goto", "objectId": "xg3xm6mhb81m6c"},
            },
            "rubber_soul": {
                RESPONSE: "{first_album}"
                "{rubber_soul} As John Lennon said, "
                "'Finally we took over the studio. In the early days, we had to take what we were given, "
                "we didn't know how you could get more bass. We were learning the technique on Rubber Soul. "
                "We took over the cover and everything.'",
                PROCESSING: [
                    loc_prs.increment_album_counter,
                    loc_prs.slot_filling_albums,
                    loc_prs.add_misc_to_response,
                ],
                TRANSITIONS: {
                    ("song", "song_q"): loc_cnd.move_on,
                    ("album", "revolver"): loc_cnd.not_visited_album,
                    ("song", "song_q", 0.1): cnd.true,
                },
                MISC: {"command": "goto", "objectId": "9wqs15r56psr2q"},
            },
            "revolver": {
                RESPONSE: "{first_album}"
                "The Beatles second-best-selling album, Revolver, "
                "was so technically complex that the band have never performed any of the songs from it live! "
                "By the way, Revolver is Pope Benedict XVI's favourite album of all times. "
                "One of the songs from it, Yellow Submarine, became an inspiration for an animated film! "
                "Have you seen it?",
                PROCESSING: [loc_prs.increment_album_counter, loc_prs.add_misc_to_response],
                TRANSITIONS: {
                    ("song", "song_q"): loc_cnd.move_on,
                    ("album", "yellow_submarine"): int_cnd.is_yes_vars,
                    ("song", "yellow_submarine"): int_cnd.is_no_vars,
                },
                MISC: {"command": "goto", "objectId": "86npm1z4m5mftr"},
            },
            "yellow_submarine": {
                RESPONSE: "{first_album} {yellow_submarine} One side of the album contains Beatles' song, "
                "while the other one consists of symphonic film score composed by George Martin, "
                "the Beatles' producer and the so-called fifth Beatle. Have you ever heard of this man?",
                PROCESSING: [
                    loc_prs.increment_album_counter,
                    loc_prs.slot_filling_albums,
                    loc_prs.add_misc_to_response,
                ],
                TRANSITIONS: {
                    ("song", "song_q"): loc_cnd.move_on,
                    ("album", "sgt_peppers"): loc_cnd.not_visited_album,
                    ("song", "song_q", 0.1): cnd.true,
                },
                MISC: {"command": "goto", "objectId": "ht5p6z4rs7zf65"},
            },
            "sgt_peppers": {
                RESPONSE: "{first_album} "
                "Called 'a decisive moment in the history of Western civilisation', "
                "'the most important and influential rock and roll album ever recorded' and "
                "'a historic departure in the progress of music', "
                "Sgt. Pepper's Lonely Hearts Club Band is the Beatles' best-selling album "
                "of all times. More than 32 million copies of "
                "Sgt. Pepper's Lonely Hearts Club Band were sold all over the world! "
                "A stunning number, isn't it?",
                PROCESSING: [
                    loc_prs.increment_album_counter,
                    loc_prs.slot_filling_albums,
                    loc_prs.add_misc_to_response,
                ],
                TRANSITIONS: {
                    ("song", "song_q"): loc_cnd.move_on,
                    ("album", "white_album"): loc_cnd.not_visited_album,
                    ("song", "song_q", 0.1): cnd.true,
                },
                MISC: {"command": "goto", "objectId": "n0kgrcdqqqfpqq"},
            },
            "white_album": {
                RESPONSE: "{first_album} Unlike the earlier period, "
                "the idea of the band's The Beatles, or the White Album, "
                "was almost entirely conceived far from London. The group went to an ashram in Rishikesh, India, "
                "for a meditation course, where they only had an acoustic guitar available! Even though the album "
                "was not critically acclaimed, Lennon said: 'I think it’s the best music we’ve ever made', "
                "however adding: 'But as a Beatles thing, as a whole, it just doesn’t work'."
                "What do you think about this album?",
                PROCESSING: [
                    loc_prs.increment_album_counter,
                    loc_prs.slot_filling_albums,
                    loc_prs.add_misc_to_response,
                ],
                TRANSITIONS: {
                    ("song", "song_q"): loc_cnd.move_on,
                    ("album", "abbey_road"): loc_cnd.not_visited_album,
                    ("song", "song_q", 0.1): cnd.true,
                },
                MISC: {"command": "goto", "objectId": "h8fxrqh4611dg3"},
            },
            "abbey_road": {
                RESPONSE: "{first_album} {abbey_road} "
                "Abbey Road's working title was Everest, but they say that the band didn't like the idea of "
                "going to Mount Everest to do a photoshoot for the cover. So they invented another title "
                "- Abbey Road, after the street where most of the band's material was recorded. By the way, "
                "do you remember what the album's cover looks like?",
                PROCESSING: [
                    loc_prs.increment_album_counter,
                    loc_prs.slot_filling_albums,
                    loc_prs.add_misc_to_response,
                ],
                TRANSITIONS: {
                    ("song", "song_q"): loc_cnd.move_on,
                    ("album", "abbey_road_cover"): int_cnd.is_no_vars,
                    ("album", "let_it_be"): loc_cnd.not_visited_album,
                    ("song", "song_q", 0.1): cnd.true,
                },
                MISC: {"command": "goto", "objectId": "665x7hc4s22wpv"},
            },
            "abbey_road_cover": {
                RESPONSE: "Then let me show it to you! The photoshoot was Paul McCartney's idea. "
                "It happened right outside the bands' "
                "recording studio and took less than half an hour.",
                PROCESSING: [loc_prs.increment_album_counter, loc_prs.add_misc_to_response],
                TRANSITIONS: {
                    ("song", "song_q"): loc_cnd.move_on,
                    ("album", "let_it_be"): loc_cnd.not_visited_album,
                    ("song", "song_q", 0.1): cnd.true,
                },
                MISC: {"command": "goto", "objectId": "z3nfvv0r06v3kx"},
            },
            "let_it_be": {
                RESPONSE: "{first_album} {let_it_be} "
                "Originally, the band's last album was called Get Back, but later its name was changed to Let It Be. "
                "The band wanted to record it live in front of an audience in an exotic location, "
                "but at last the recording took place in a studio. The album spent more than a year unreleased "
                "as the relations between the Beatles had become so tense "
                "that none of them wanted to sort the songs out.",
                PROCESSING: [
                    loc_prs.increment_album_counter,
                    loc_prs.slot_filling_albums,
                    loc_prs.add_misc_to_response,
                ],
                TRANSITIONS: {
                    ("song", "song_q"): loc_cnd.move_on,
                    ("album", "please_please_me"): loc_cnd.not_visited_album,
                    ("song", "song_q", 0.1): cnd.true,
                },
                MISC: {"command": "goto", "objectId": "4n02cf8h4qx00c"},
            },
        },
    },
    "photos": {
        GRAPH: {
            "photos_q": {
                RESPONSE: "Would you like to see some pictures of The Beatles?",
                TRANSITIONS: {("photos", "abbey_road"): int_cnd.is_yes_vars},
            },
            "abbey_road": {
                RESPONSE: """Here! It's the only original Beatles album cover to show neither the artist name nor"""
                """the album title. Do you remember the name of this album?""",
                PROCESSING: [loc_prs.add_misc_to_response],
                TRANSITIONS: {("photos", "fact_ar"): loc_cnd.has_correct_answer, ("photos", "info_ar"): cnd.true},
                MISC: {"command": "goto", "objectId": "b9d08nbdvh8vsb"},
            },
            "fact_ar": {
                RESPONSE: """Yes, it's Abbey Road!! Did you know that after the album was released, the number plate """
                """"(LMW 281F) was repeatedly stolen from the white Volkswagen Beetle from the picture? Poor owner"""
                """of the car...""",
                TRANSITIONS: {("photos", "yesterday&today"): cnd.true},
            },
            "info_ar": {
                RESPONSE: "It's Abbey Road! Photographer was given only 10 minutes to take the photo while he stood "
                """on a step-ladder and a policeman held up traffic behind the camera. He took 6 photographs and """
                """McCartney chose this one for the cover""",
                TRANSITIONS: {("photos", "yesterday&today"): cnd.true},
            },
            "yesterday&today": {
                RESPONSE: """This photo is from Whitaker photo session, where he assembled different scary props such"""
                """as doll parts and trays of meat. One of the photos was used for the cover of Yesterday """
                """and Today album. We have some more photos of The Beatles, so be sure to check them out 🙂 """,
                PROCESSING: [loc_prs.add_misc_to_response],
                MISC: {"command": "goto", "objectId": "pv2qgzk51vmgq6"},
            },
        },
    },
    "song": {
        GRAPH: {
            "song_q": {
                RESPONSE: "All right, let's finish the albums here. What's your favorite Beatles song?",
                TRANSITIONS: {("song", "fav_song"): loc_cnd.has_songs, ("song", "why_song"): cnd.true},
            },
            "fav_song": {
                RESPONSE: "Oh, have you seen the music video for this song?",
                PROCESSING: [loc_prs.extract_song_id, loc_prs.add_misc_to_response],
                TRANSITIONS: {("album", "who_beatle"): int_cnd.is_yes_vars, ("song", "watch_video"): cnd.true},
            },
            "watch_video": {
                RESPONSE: "Do you want to watch it?",
                TRANSITIONS: {("song", "show_video"): int_cnd.is_yes_vars, ("album", "who_beatle"): cnd.true},
            },
            "show_video": {
                RESPONSE: "Great! You can watch it 🙂 " "Just text me when you're done",
                PROCESSING: [loc_prs.add_misc_to_response],
                TRANSITIONS: {("album", "who_beatle"): cnd.true},
                MISC: {"command": "goto", "objectId": "{video}"},
            },
            "why_song": {RESPONSE: "Why do you like this song?", TRANSITIONS: {("album", "who_beatle"): cnd.true}},
            "yellow_submarine": {
                RESPONSE: "Then let's watch a short video and after that you can watch the entire movie if you want! "
                "Just text me when you're done.",
                PROCESSING: [loc_prs.add_misc_to_response],
                TRANSITIONS: {
                    ("song", "song_q"): loc_cnd.move_on,
                    ("album", "yellow_submarine"): loc_cnd.not_visited_album,
                    ("song", "song_q", 0.1): cnd.true,
                },
                MISC: {"command": "goto", "objectId": "86hcq66wcfgszf"},
            },
        },
    },
    "people": {
        GRAPH: {
            "name": {
                RESPONSE: "Yeah, I like {beatles_member} too! Do you want to take a look at his biography?",
                PROCESSING: [loc_prs.extract_members, loc_prs.fill_slots],
                TRANSITIONS: {("people", "bio"): int_cnd.is_yes_vars, ("beatles", "instruments_q"): cnd.true},
            },
            "bio": {
                RESPONSE: "Here! Text me when you're done :)",
                TRANSITIONS: {("beatles", "instruments_q"): cnd.true},
                MISC: {"command": "goto", "objectId": "{beatles_member}"},
            },
            "fact_lennon": {
                RESPONSE: "Yeah, I like {beatles_member} too! By the way, did you know that John Lennon’s father"
                " was absent for much of his early life but showed up when his son became famous?"
                " Sounds kind of sad... Do you want to take a look at his biography?",
                PROCESSING: [loc_prs.extract_members, loc_prs.fill_slots],
                TRANSITIONS: {("people", "bio"): int_cnd.is_yes_vars, ("beatles", "instruments_q"): cnd.true},
            },
            "fact_mccartney": {
                RESPONSE: "Yeah, I like {beatles_member} too! By the way, did you know that Paul McCartney played"
                " to what's believed to be the largest paid audience in recorded history? In 1989,"
                " he played a solo concert to a crowd of 350,000-plus in Brazil. That's amazing!"
                "Do you want to take a look at his biography?",
                PROCESSING: [loc_prs.extract_members, loc_prs.fill_slots],
                TRANSITIONS: {("people", "bio"): int_cnd.is_yes_vars, ("beatles", "instruments_q"): cnd.true},
            },
            "fact_harrison": {
                RESPONSE: "Yeah, I like {beatles_member} too! By the way, did you know that"
                " the song ‘CRACKERBOX PALACE’ is about his mansion?  Modest as he was - he did live"
                " in a 120 room mansion on a 66 acre estate. Do you want to take a look at his biography?",
                PROCESSING: [loc_prs.extract_members, loc_prs.fill_slots],
                TRANSITIONS: {("people", "bio"): int_cnd.is_yes_vars, ("beatles", "instruments_q"): cnd.true},
            },
            "fact_starr": {
                RESPONSE: "Yeah, I like {beatles_member} too! By the way, did you know that due to his allergy"
                " he has never had pizza, curry, or onions? That didn’t stop him from doing a pizza"
                " commercial in 1995, though. Do you want to take a look at his biography?",
                PROCESSING: [loc_prs.extract_members, loc_prs.fill_slots],
                TRANSITIONS: {("people", "bio"): int_cnd.is_yes_vars, ("beatles", "instruments_q"): cnd.true},
            },
        },
    },
    "instruments": {
        GRAPH: {
            "guitar": {RESPONSE: "Cool! I can show you Paul McCartney's guitar!"},
            "play_q": {
                RESPONSE: "And do you play any instrument?",
                TRANSITIONS: {
                    ("instruments", "guitar_paul_1"): int_cnd.is_yes_vars,
                    ("instruments", "guitar_paul_1_2"): cnd.true,
                },
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
                PROCESSING: [loc_prs.extract_inst, loc_prs.fill_slots, loc_prs.add_misc_to_response],
                TRANSITIONS: {("instruments", "guitar_paul_2"): cnd.true},
                MISC: {"command": "goto", "objectId": "f47z2rzm0tt4b8"},
            },
            "guitar_paul_1_2": {
                RESPONSE: "I can show you Paul McCartney's guitar!"
                "In 1956, McCartney's father gave him a trumpet for his birthday. "
                """But, as Paul said later, "you couldn't sing with a trumpet stuck in your mouth", """
                "so he traded it for Zenith Model 17 acoustic. Let's have a look at it. "
                "At first, Paul couldn't figure out how to play it, but then he realized that "
                "he had to hold the guitar differently as he was left-handed. Isn't it beautiful?",
                PROCESSING: [loc_prs.add_misc_to_response],
                TRANSITIONS: {("instruments", "guitar_paul_2"): cnd.true},
                MISC: {"command": "goto", "objectId": "f47z2rzm0tt4b8"},
            },
            "guitar_paul_2": {
                RESPONSE: " And here is Paul's Hofner 500/1 bass. "
                """He went with this Hofner from "I Want to Hold Your Hand" through "Let It Be" and beyond. """
                "Do you want to take a look at one of John Lennon's guitars?",
                PROCESSING: [loc_prs.add_misc_to_response],
                TRANSITIONS: {("instruments", "guitar_lennon"): int_cnd.is_yes_vars, ("photos", "photos_q"): cnd.true},
                MISC: {"command": "goto", "objectId": "r369t7g5cw3x0h"},
            },
            "guitar_lennon": {
                RESPONSE: "Look! It's Lennon's Rickenbacker 325! He had four models of this guitar. Do you like it?",
                PROCESSING: [loc_prs.add_misc_to_response],
                TRANSITIONS: {("instruments", "drum_kit"): cnd.true},
                MISC: {"command": "goto", "objectId": "07ptwckzth85qz"},
            },
            "drum_kit": {
                RESPONSE: "Well, now that you've seen the guitars it's time to look at Ringo Starr's "
                "drum kit. During his time in The Beatles, he played six different drum kits, "
                "five of which were from Ludwig.",
                PROCESSING: [loc_prs.add_misc_to_response],
                TRANSITIONS: {("photos", "photos_q"): cnd.true},
                MISC: {"command": "goto", "objectId": "vx6bwczc94mtpq"},
            },
        }
    },
}


actor = Actor(flows, start_node_label=("beatles", "start"))
