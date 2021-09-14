import logging
import re

from dff.core.keywords import TRANSITIONS, GRAPH, RESPONSE, GLOBAL_TRANSITIONS, PROCESSING, MISC
from dff.core import Actor
from dff.core import Context
import dff.conditions as cnd
import dff.transitions as trn
from typing import Optional

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
        GLOBAL_TRANSITIONS: {("beatles", "beatles_q", 1.2): cnd.regexp(r"\bbeatles\b", re.I),
                             trn.previous(1.2): cnd.regexp(r".*(sorry)|(repeat)|(go\sback)|(previous).*", re.I),
                             ("beatles_reset", "intro_reset", 1.2): cnd.regexp(r"\breset\b", re.I),
                             ("album", "please_please_me", 1.2): loc_cnd.wants_to_see(item_name="Please Please Me"),
                             ("album", "with_the_beatles", 1.2): loc_cnd.wants_to_see(item_name="With The Beatles"),
                             ("album", "a_hard_days_night_wrong", 1.2): loc_cnd.wants_to_see(item_name="Hard Day's Night"),
                             ("album", "beatles_for_sale", 1.2): loc_cnd.wants_to_see(item_name="Beatles For Sale"),
                             ("album", "rubber_soul", 1.2): loc_cnd.wants_to_see(item_name="Rubber Soul"),
                             ("album", "revolver", 1.2): loc_cnd.wants_to_see(item_name="Revolver"),
                             ("album", "yellow_submarine", 1.2): loc_cnd.wants_to_see(item_name="Yellow Submarine"),
                             ("album", "sgt_peppers", 1.2): loc_cnd.wants_to_see(
                                 item_name="Sgt. Pepper's Lonely Hearts Club Band"),
                             ("album", "white_album", 1.2): loc_cnd.wants_to_see(item_name="White Album"),
                             ("album", "abbey_road", 1.2): loc_cnd.wants_to_see(item_name="Abbey Road"),
                             ("album", "let_it_be", 1.2): loc_cnd.wants_to_see(item_name="Let It Be"),
                             ("album", "who_beatle_res", 1.2): loc_cnd.wants_to_see(
                                 item_name=['beatles', 'band members', "artists", "the band", "band"]),
                             ("song", "video_q", 1.2): loc_cnd.wants_to_see(item_name=["songs", "videos"]),
                             ("photos", "abbey_road", 1.2): loc_cnd.wants_to_see(item_name=["photos", "pictures"]),
                             ("album", "what_album_res", 1.2): loc_cnd.wants_to_see(item_name="albums"),
                             ("instruments", "play_q_res", 1.2): loc_cnd.wants_to_see(item_name="instruments"),
                             ("album", "help", 1.2): loc_cnd.wants_to_see(item_name="Help!"),
                             ("instruments", "guitar_paul_1", 1.2): loc_cnd.wants_to_see(item_name=["zenith", "paul's guitar", "mccartney's guitar"]),
                             ("instruments", "guitar_paul_2", 1.2): loc_cnd.wants_to_see(item_name="hofner"),
                             ("instruments", "guitar_lennon", 1.2): loc_cnd.wants_to_see(item_name=["john's guitar", "lennon's guitar", "rickenbacker"]),
                             ("instruments", "drum_kit", 1.2): loc_cnd.wants_to_see(item_name=["drum kit", "drums"]),
                             ("people", "fact_lennon", 1.2): loc_cnd.wants_to_see(item_name=['John', 'Lennon']),
                             ("people", "fact_mccartney", 1.2): loc_cnd.wants_to_see(item_name=['Paul', 'McCartney']),
                             ("people", "fact_starr", 1.2): loc_cnd.wants_to_see(item_name=['Ringo', 'Starr']),
                             ("people", "fact_harrison", 1.2): loc_cnd.wants_to_see(item_name=['George', 'Harrison']),
                             ("history", "first_members_res", 1.2): loc_cnd.wants_to_see(item_name='history'),
                             ("beatles_reset", "sorry_reset", 1.2): cnd.regexp(r"((.*i\swant\sto\ssee\s)|(.*go\sto.*)|"
                                                                               r"(.*i\swanna\ssee\s)|(.*\slook\sat\s)|"
                                                                               r"(.*show\sme\s)|(.*tell\sme))", re.I),
                             },
        GRAPH: {
            "start": {RESPONSE: "Hello!"},
            "beatles_q": {
                RESPONSE: "Hello! I am the Doorman and I will be your guide here today. Do you like Beatles?",
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
                    # trn.previous(): cnd.regexp(r".*(sorry)|(repeat)|(go\sback)|(previous).*", re.I),
                    ("instruments", "play_q"): int_cnd.is_yes_vars,
                    ("photos", "photos_q"): cnd.true,
                },
            },
        },
    },
    "beatles_reset": {
        GRAPH: {
            "intro_reset": {
                RESPONSE: "Hello, again! What do you want to discuss about the Beatles? "
                          "Ask me to tell about albums, instruments, songs, the band's history or artists themselves.",
                TRANSITIONS: {
                    # trn.previous(): cnd.regexp(r".*(sorry)|(repeat)|(go\sback)|(previous).*", re.I),
                    ("album", "what_album"): cnd.regexp(r".*album.*", re.I),
                    ("instruments", "play_q"): cnd.regexp(r".*instrument.*", re.I),
                    ("song", "video_q"): cnd.regexp(r".*song.*", re.I),
                    ("album", "who_beatle"): cnd.regexp(r".*artist.*", re.I),
                    ("history", "first_members_res"): cnd.regexp(r".*history.*", re.I)
                },
            },
            "sorry_reset": {
                RESPONSE: "Sorry, I would love to help you with that, but I am not ready yet. "
                          "You can ask me to tell about albums, instruments, songs, the band's history or artists themselves.",
                TRANSITIONS: {
                    # trn.previous(): cnd.regexp(r".*(sorry)|(repeat)|(go\sback)|(previous).*", re.I),
                    ("album", "what_album"): cnd.regexp(r".*album.*", re.I),
                    ("instruments", "play_q"): cnd.regexp(r".*instrument.*", re.I),
                    ("song", "video_q"): cnd.regexp(r".*song.*", re.I),
                    ("album", "who_beatle"): cnd.regexp(r".*artist.*", re.I),
                    ("history", "first_members_res"): cnd.regexp(r".*history.*", re.I)
                },
            },
        },
    },
    "beatles_fact": {
        GRAPH: {
            "name": {
                RESPONSE: "Beatles... Sounds like a wordplay, doesn’t it? Beetles making the beat. "
                "That’s how they meant it.",
                TRANSITIONS: {
                    trn.previous(): cnd.regexp(r".*(sorry)|(repeat)|(go\sback)|(previous).*", re.I),
                    ("history", "first_members"): cnd.true},
            }
        },
    },
    "history": {
        GRAPH: {
            "first_members": {
                RESPONSE: "First, I will tell you about the band's history. If you get tired, you can tell me to 'move on' "
                          "and I will take you to the next part. "
                          "The band formed around John Lennon and Paul McCartney, who first performed together in 1957. "
                          "Do you know in what city the story of the Beatles began?",
                TRANSITIONS: {
                    # trn.previous(): cnd.regexp(r".*(sorry)|(repeat)|(go\sback)|(previous).*", re.I),
                    ("album", "what_album"): loc_cnd.move_on,
                    ("what_is_next", "cur_history"): cnd.regexp(r"\bwhat's\snext\b", re.I),
                    ("history", "city_right"): loc_cnd.has_album(album_name="Liverpool"),
                    ("history", "city_wrong"): cnd.true
                },
            },
            "first_members_res": {
                RESPONSE: "The Beatles formed around John Lennon and Paul McCartney, who first performed together in 1957. "
                          "Do you know in what city the story of the band began?",
                TRANSITIONS: {
                    # trn.previous(): cnd.regexp(r".*(sorry)|(repeat)|(go\sback)|(previous).*", re.I),
                    ("album", "what_album"): loc_cnd.move_on,
                    ("what_is_next", "cur_history"): cnd.regexp(r"\bwhat's\snext\b", re.I),
                    ("history", "city_right"): loc_cnd.has_album(album_name="Liverpool"),
                    ("history", "city_wrong"): cnd.true
                },
            },
            "city_wrong": {
                RESPONSE: "It was Liverpool! The 'beat' music scene was booming there at that moment. "
                          "The band also used to perform a lot in Hamburg. And do you know who was the Beatles' "
                          "first drummer? ",
                TRANSITIONS: {
                    # trn.previous(): cnd.regexp(r".*(sorry)|(repeat)|(go\sback)|(previous).*", re.I),
                    ("album", "what_album"): loc_cnd.move_on,
                    ("what_is_next", "cur_history"): cnd.regexp(r"\bwhat's\snext\b", re.I),
                    ("history", "drummer_right"): loc_cnd.has_album(album_name=["Pete", "Best"]),
                    ("history", "drummer_wrong"): cnd.true
                },
            },
            "city_right": {
                RESPONSE: "Wow, you seem to know a lot about the band! And do you know who was the Beatles' "
                          "first drummer? ",
                TRANSITIONS: {
                    # trn.previous(): cnd.regexp(r".*(sorry)|(repeat)|(go\sback)|(previous).*", re.I),
                    ("album", "what_album"): loc_cnd.move_on,
                    ("what_is_next", "cur_history"): cnd.regexp(r"\bwhat's\snext\b", re.I),
                    ("history", "drummer_right"): loc_cnd.has_album(album_name=["Pete", "Best"]),
                    ("history", "drummer_wrong"): cnd.true
                },
            },
            "drummer_wrong": {
                RESPONSE: "His name was Pete Best. John Lennon, Paul McCartney, George Harrison "
                          "and Pete Best were the first Beatles. But later the band fell out with Pete and that was "
                          "when they invited Ringo Starr to play with them. Now let's move on and talk about albums!",
                TRANSITIONS: {
                    # trn.previous(): cnd.regexp(r".*(sorry)|(repeat)|(go\sback)|(previous).*", re.I),
                    ("album", "what_album"): loc_cnd.move_on,
                    ("album", "what_album"): cnd.true
                },
            },
            "drummer_right": {
                RESPONSE: "Yeah, that was him! After several years of playing with other bands, Pete worked as a civil "
                          "servant for 20 years. Now he has a band of his own, Pete Best Band. Now let's move on "
                          "and talk about albums. ",
                TRANSITIONS: {
                    # trn.previous(): cnd.regexp(r".*(sorry)|(repeat)|(go\sback)|(previous).*", re.I),
                    ("album", "what_album"): cnd.true},
            }
        },
    },
    "album": {
        GRAPH: {
            "what_album": {
                RESPONSE: "What's your favorite Beatles album?",
                PROCESSING: [loc_prs.add_node_name(name='what_album')],
                TRANSITIONS: {
                    # trn.previous(): cnd.regexp(r".*(sorry)|(repeat)|(go\sback)|(previous).*", re.I),
                    ("album", "please_please_me"): loc_cnd.has_album(album_name="Please Please Me"),
                    ("album", "with_the_beatles"): loc_cnd.has_album(album_name="With The Beatles"),
                    ("album", "a_hard_days_night_wrong"): loc_cnd.has_album(album_name="Hard Day's Night"),
                    ("album", "beatles_for_sale"): loc_cnd.has_album(album_name="Beatles For Sale"),
                    ("album", "rubber_soul"): loc_cnd.has_album(album_name="Rubber Soul"),
                    ("album", "revolver"): loc_cnd.has_album(album_name="Revolver"),
                    ("album", "yellow_submarine"): loc_cnd.has_album(album_name="Yellow Submarine"),
                    ("album", "sgt_peppers"): loc_cnd.has_album(album_name="Sgt. Pepper's Lonely Hearts Club Band"),
                    ("album", "white_album"): loc_cnd.has_album(album_name="White Album"),
                    ("album", "abbey_road"): loc_cnd.has_album(album_name="Abbey Road"),
                    ("album", "let_it_be"): loc_cnd.has_album(album_name="Let It Be"),
                    ("album", "help"): loc_cnd.has_album(album_name="Help"),
                    ("album", "please_please_me"): cnd.true,
                },
            },
            "what_album_res": {
                RESPONSE: "What album do you want to begin with?",
                TRANSITIONS: {
                    # trn.previous(): cnd.regexp(r".*(sorry)|(repeat)|(go\sback)|(previous).*", re.I),
                    ("album", "please_please_me"): loc_cnd.has_album(album_name="Please Please Me"),
                    ("album", "with_the_beatles"): loc_cnd.has_album(album_name="With The Beatles"),
                    ("album", "a_hard_days_night_wrong"): loc_cnd.has_album(album_name="Hard Day's Night"),
                    ("album", "beatles_for_sale"): loc_cnd.has_album(album_name="Beatles For Sale"),
                    ("album", "rubber_soul"): loc_cnd.has_album(album_name="Rubber Soul"),
                    ("album", "revolver"): loc_cnd.has_album(album_name="Revolver"),
                    ("album", "yellow_submarine"): loc_cnd.has_album(album_name="Yellow Submarine"),
                    ("album", "sgt_peppers"): loc_cnd.has_album(album_name="Sgt. Pepper's Lonely Hearts Club Band"),
                    ("album", "white_album"): loc_cnd.has_album(album_name="White Album"),
                    ("album", "abbey_road"): loc_cnd.has_album(album_name="Abbey Road"),
                    ("album", "let_it_be"): loc_cnd.has_album(album_name="Let It Be"),
                    ("album", "help"): loc_cnd.has_album(album_name="Help"),
                    ("album", "please_please_me"): cnd.true,
                },
            },
            "who_beatle": {
                RESPONSE: "By the way, who is your favorite Beatle?",
                TRANSITIONS: {
                    # trn.previous(): cnd.regexp(r".*(sorry)|(repeat)|(go\sback)|(previous).*", re.I),
                    ("what_is_next", "cur_band"): cnd.regexp(r"\bwhat's\snext\b", re.I),
                    ("people", "fact_lennon"): loc_cnd.has_member(member_name=['John', 'Lennon']),
                    ("people", "fact_mccartney"): loc_cnd.has_member(member_name=['Paul', 'McCartney']),
                    ("people", "fact_starr"): loc_cnd.has_member(member_name=['Ringo', 'Starr']),
                    ("people", "fact_harrison"): loc_cnd.has_member(member_name=['George', 'Harrison']),
                    ("beatles", "instruments_q"): cnd.true,
                },
            },
            "who_beatle_res": {
                RESPONSE: "Who do you want to discuss: John, Paul, Ringo or George?",
                TRANSITIONS: {
                    # trn.previous(): cnd.regexp(r".*(sorry)|(repeat)|(go\sback)|(previous).*", re.I),
                    ("what_is_next", "cur_band"): cnd.regexp(r"\bwhat's\snext\b", re.I),
                    ("people", "fact_lennon"): loc_cnd.has_member(member_name=['John', 'Lennon']),
                    ("people", "fact_mccartney"): loc_cnd.has_member(member_name=['Paul', 'McCartney']),
                    ("people", "fact_starr"): loc_cnd.has_member(member_name=['Ringo', 'Starr']),
                    ("people", "fact_harrison"): loc_cnd.has_member(member_name=['George', 'Harrison']),
                    ("beatles", "instruments_q"): cnd.true,
                },
            },
	        "who_beatle_1": {
                RESPONSE: "Well, I am not sure that this song is The Beatles' song... By the way, who is your favorite Beatle?",
                TRANSITIONS: {
                    # trn.previous(): cnd.regexp(r".*(sorry)|(repeat)|(go\sback)|(previous).*", re.I),
                    ("what_is_next", "cur_band"): cnd.regexp(r"\bwhat's\snext\b", re.I),
                    ("people", "fact_lennon"): loc_cnd.has_member(member_name=['John', 'Lennon']),
                    ("people", "fact_mccartney"): loc_cnd.has_member(member_name=['Paul', 'McCartney']),
                    ("people", "fact_starr"): loc_cnd.has_member(member_name=['Ringo', 'Starr']),
                    ("people", "fact_harrison"): loc_cnd.has_member(member_name=['George', 'Harrison']),
                    ("beatles", "instruments_q"): cnd.true,
                },
            },
            "please_please_me": {
                RESPONSE: "{first_album}Please Please Me is the first studio album by the Beatles! "
                "The album was recorded within 13 hours and the studio cost 400£. "
                "It hit the top of the British chart and stayed there for 30 weeks to be replaced "
                "by 'With the Beatles'. Quite unexpected for a debut, right?",
                PROCESSING: [
                    loc_prs.increment_album_counter,
                    loc_prs.slot_filling_albums,
                    loc_prs.add_misc_to_response,
                    loc_prs.add_node_name('Please Please Me')
                ],
                TRANSITIONS: {
                    # trn.previous(): cnd.regexp(r".*(sorry)|(repeat)|(go\sback)|(previous).*", re.I),
                    ("song", "song_q", 0.2): loc_cnd.move_on,
                    ("what_is_next", "cur_album", 0.1): cnd.regexp(r"\bwhat's\snext\b", re.I),
                    ("album", "with_the_beatles", 0.1): loc_cnd.not_visited_album,
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
                    loc_prs.add_node_name('With The Beatles')
                ],
                TRANSITIONS: {
                    # trn.previous(): cnd.regexp(r".*(sorry)|(repeat)|(go\sback)|(previous).*", re.I),
                    ("song", "song_q", 0.2): loc_cnd.move_on,
                    ("what_is_next", "cur_album", 0.1): cnd.regexp(r"\bwhat's\snext\b", re.I),
                    ("album", "a_hard_days_night_corr", 0.1): loc_cnd.has_correct_answer,
                    ("album", "a_hard_days_night_wrong", 0.1): cnd.true,
                },
                MISC: {"command": "goto", "objectId": "80nrsg1xgqk8ch"},
            },
            "a_hard_days_night_corr": {
                RESPONSE: "{a_hard_days_night_corr}{first_album}"
                "It was the band's third album, the first one to consist entirely of the Beatles' original song and \
                the only one to consist solely of songs written by Lennon-McCartney. ",
                PROCESSING: [
                    loc_prs.increment_album_counter,
                    loc_prs.slot_filling_albums,
                    loc_prs.add_misc_to_response,
                    loc_prs.add_node_name("Hard Day's Night")
                ],
                TRANSITIONS: {
                    # trn.previous(): cnd.regexp(r".*(sorry)|(repeat)|(go\sback)|(previous).*", re.I),
                    ("song", "song_q", 0.2): loc_cnd.move_on,
                    ("what_is_next", "cur_album", 0.1): cnd.regexp(r"\bwhat's\snext\b", re.I),
                    ("album", "beatles_for_sale", 0.1): loc_cnd.not_visited_album,
                    ("song", "song_q", 0.1): cnd.true,
                },
                MISC: {"command": "goto", "objectId": "2mm0prqv0rq7dh"},
            },
            "a_hard_days_night_wrong": {
                RESPONSE: "{a_hard_days_night_wrong}{first_album}"
                "It was the band's third album, the first one to consist entirely of "
                "the Beatles' original song and the only one to consist solely of songs written by Lennon-McCartney. ",
                PROCESSING: [
                    loc_prs.increment_album_counter,
                    loc_prs.slot_filling_albums,
                    loc_prs.add_misc_to_response,
                    loc_prs.add_node_name("Hard Day's Night")
                ],
                TRANSITIONS: {
                    # trn.previous(): cnd.regexp(r".*(sorry)|(repeat)|(go\sback)|(previous).*", re.I),
                    ("song", "song_q", 0.2): loc_cnd.move_on,
                    ("what_is_next", "cur_album", 0.1): cnd.regexp(r"\bwhat's\snext\b", re.I),
                    ("album", "beatles_for_sale", 0.1): loc_cnd.not_visited_album,
                    ("song", "song_q", 0.1): cnd.true,
                },
                MISC: {"command": "goto", "objectId": "2mm0prqv0rq7dh"},
            },
            "beatles_for_sale": {
                RESPONSE: "{first_album}"
                "Paul McCartney later said about the group's fourth album: "
                "'Recording Beatles For Sale didn’t take long. Basically it was our stage show, with some new songs.'",
                PROCESSING: [
                    loc_prs.increment_album_counter,
                    loc_prs.slot_filling_albums,
                    loc_prs.add_misc_to_response,
                    loc_prs.add_node_name('Beatles For Sale')
                ],
                TRANSITIONS: {
                    # trn.previous(): cnd.regexp(r".*(sorry)|(repeat)|(go\sback)|(previous).*", re.I),
                    ("song", "song_q", 0.2): loc_cnd.move_on,
                    ("what_is_next", "cur_album", 0.1): cnd.regexp(r"\bwhat's\snext\b", re.I),
                    ("album", "help", 0.1): loc_cnd.not_visited_album,
                    ("song", "song_q", 0.1): cnd.true,
                },
                MISC: {"command": "goto", "objectId": "w2gnmmg1f34rkh"},
            },
            "help": {
                RESPONSE: "{first_album}"
                "Just like A Hard Day's Night, one side of Help! consisted of the soundtrack songs for the movie. "
                "The other side included several famous songs, such as Yesterday. John Lennon later said that the title song "
                "of the album really was a cry for help: 'I was fat and depressed and I was crying out for 'Help'.'",
                PROCESSING: [
                    loc_prs.increment_album_counter,
                    loc_prs.slot_filling_albums,
                    loc_prs.add_misc_to_response,
                    loc_prs.add_node_name('Help')
                ],
                TRANSITIONS: {
                    # trn.previous(): cnd.regexp(r".*(sorry)|(repeat)|(go\sback)|(previous).*", re.I),
                    ("song", "song_q", 0.2): loc_cnd.move_on,
                    ("what_is_next", "cur_album", 0.1): cnd.regexp(r"\bwhat's\snext\b", re.I),
                    ("album", "rubber_soul", 0.1): loc_cnd.not_visited_album,
                    ("song", "song_q", 0.1): cnd.true,
                },
                MISC: {"command": "goto", "objectId": "xg3xm6mhb81m6c"},
            },
            "rubber_soul": {
                RESPONSE: "{first_album}"
                "{rubber_soul} As John Lennon said about this album, "
                "'Finally we took over the studio. In the early days, we had to take what we were given, "
                "we didn't know how you could get more bass. We were learning the technique on Rubber Soul.'",
                PROCESSING: [
                    loc_prs.increment_album_counter,
                    loc_prs.slot_filling_albums,
                    loc_prs.add_misc_to_response,
                    loc_prs.add_node_name('Rubber Soul')
                ],
                TRANSITIONS: {
                    # trn.previous(): cnd.regexp(r".*(sorry)|(repeat)|(go\sback)|(previous).*", re.I),
                    ("song", "song_q", 0.2): loc_cnd.move_on,
                    ("what_is_next", "cur_album", 0.1): cnd.regexp(r"\bwhat's\snext\b", re.I),
                    ("album", "revolver", 0.1): loc_cnd.not_visited_album,
                    ("song", "song_q", 0.1): cnd.true,
                },
                MISC: {"command": "goto", "objectId": "9wqs15r56psr2q"},
            },
            "revolver": {
                RESPONSE: "{first_album}"
                "Revolver was so technically complex that the band has never performed any of the songs from it live! "
                "By the way, Revolver is Pope Benedict XVI's favourite album of all times. "
                "Yellow Submarine, a song from it, became an inspiration for an animated film! "
                "Have you seen it?",
                PROCESSING: [
                    loc_prs.increment_album_counter,
                    loc_prs.slot_filling_albums,
                    loc_prs.add_misc_to_response,
                    loc_prs.add_node_name('Revolver')
                ],
                TRANSITIONS: {
                    # trn.previous(): cnd.regexp(r".*(sorry)|(repeat)|(go\sback)|(previous).*", re.I),
                    ("song", "song_q", 0.2): loc_cnd.move_on,
                    ("what_is_next", "cur_album", 0.1): cnd.regexp(r"\bwhat's\snext\b", re.I),
                    ("song", "yellow_submarine", 0.1): int_cnd.is_no_vars,
                    ("album", "yellow_submarine", 0.1): cnd.true,
                },
                MISC: {"command": "goto", "objectId": "86npm1z4m5mftr"},
            },
            "yellow_submarine": {
                RESPONSE: "{yellow_submarine}{first_album}One side of the album contains Beatles' song, "
                "while the other one consists of symphonic film score composed by George Martin, "
                "the Beatles' producer and the so-called fifth Beatle. Have you ever heard of this man?",
                PROCESSING: [
                    loc_prs.increment_album_counter,
                    loc_prs.slot_filling_albums,
                    loc_prs.add_misc_to_response,
                    loc_prs.add_node_name('Yellow Submarine')
                ],
                TRANSITIONS: {
                    # trn.previous(): cnd.regexp(r".*(sorry)|(repeat)|(go\sback)|(previous).*", re.I),
                    ("song", "song_q", 0.2): loc_cnd.move_on,
                    ("what_is_next", "cur_album", 0.1): cnd.regexp(r"\bwhat's\snext\b", re.I),
                    ("album", "sgt_peppers", 0.1): loc_cnd.not_visited_album,
                    ("song", "song_q", 0.1): cnd.true,
                },
                MISC: {"command": "goto", "objectId": "ht5p6z4rs7zf65"},
            },
            "sgt_peppers": {
                RESPONSE: "{sgt_peppers}{first_album}"
                "Called 'a decisive moment in the history of Western civilisation', "
                "Sgt. Pepper's Lonely Hearts Club Band is the Beatles' best-selling album "
                "of all times. More than 32 million copies were sold all over the world! "
                "A stunning number, isn't it?",
                PROCESSING: [
                    loc_prs.increment_album_counter,
                    loc_prs.slot_filling_albums,
                    loc_prs.add_misc_to_response,
                    loc_prs.add_node_name("Sgt. Pepper's Lonely Hearts Club Band")
                ],
                TRANSITIONS: {
                    # trn.previous(): cnd.regexp(r".*(sorry)|(repeat)|(go\sback)|(previous).*", re.I),
                    ("song", "song_q", 0.2): loc_cnd.move_on,
                    ("what_is_next", "cur_album", 0.1): cnd.regexp(r"\bwhat's\snext\b", re.I),
                    ("album", "white_album", 0.1): loc_cnd.not_visited_album,
                    ("song", "song_q", 0.1): cnd.true,
                },
                MISC: {"command": "goto", "objectId": "n0kgrcdqqqfpqq"},
            },
            "white_album": {
                RESPONSE: "{first_album}Unlike the earlier albums, "
                "the idea of 'The Beatles', or the White Album, "
                "was almost entirely conceived far from London. The group went to an ashram in Rishikesh, India, "
                "for a meditation course, where they only had an acoustic guitar available! "
                "What do you think about this album?",
                PROCESSING: [
                    loc_prs.increment_album_counter,
                    loc_prs.slot_filling_albums,
                    loc_prs.add_misc_to_response,
                    loc_prs.add_node_name('White Album')
                ],
                TRANSITIONS: {
                    # trn.previous(): cnd.regexp(r".*(sorry)|(repeat)|(go\sback)|(previous).*", re.I),
                    ("song", "song_q", 0.2): loc_cnd.move_on,
                    ("what_is_next", "cur_album", 0.1): cnd.regexp(r"\bwhat's\snext\b", re.I),
                    ("album", "abbey_road", 0.1): loc_cnd.not_visited_album,
                    ("song", "song_q", 0.1): cnd.true,
                },
                MISC: {"command": "goto", "objectId": "h8fxrqh4611dg3"},
            },
            "abbey_road": {
                RESPONSE: "{abbey_road}{first_album}"
                "Abbey Road's working title was Everest, but it seems that the band didn't want to go "
                "to Mount Everest to do a photoshoot for the cover. So they named it "
                "after the street where most of the band's material was recorded.",
                PROCESSING: [
                    loc_prs.increment_album_counter,
                    loc_prs.slot_filling_albums,
                    loc_prs.add_misc_to_response,
                    loc_prs.add_node_name('Abbey Road')
                ],
                TRANSITIONS: {
                    # trn.previous(): cnd.regexp(r".*(sorry)|(repeat)|(go\sback)|(previous).*", re.I),
                    ("song", "song_q", 0.2): loc_cnd.move_on,
                    ("what_is_next", "cur_album", 0.1): cnd.regexp(r"\bwhat's\snext\b", re.I),
                    ("album", "let_it_be", 0.1): loc_cnd.not_visited_album,
                    ("song", "song_q", 0.1): cnd.true,
                },
                MISC: {"command": "goto", "objectId": "665x7hc4s22wpv"},
            },
            "let_it_be": {
                RESPONSE: "{let_it_be}{first_album}"
                "Originally, the band's last album was called Get Back, but later its name was changed to Let It Be. "
                "The album spent more than a year unreleased as the relations between the Beatles had become so tense "
                "that none of them wanted to sort the songs out.",
                PROCESSING: [
                    loc_prs.increment_album_counter,
                    loc_prs.slot_filling_albums,
                    loc_prs.add_misc_to_response,
                    loc_prs.add_node_name('Let It Be')
                ],
                TRANSITIONS: {
                    # trn.previous(): cnd.regexp(r".*(sorry)|(repeat)|(go\sback)|(previous).*", re.I),
                    ("song", "song_q", 0.2): loc_cnd.move_on,
                    ("what_is_next", "cur_album", 0.1): cnd.regexp(r"\bwhat's\snext\b", re.I),
                    ("album", "please_please_me", 0.1): loc_cnd.not_visited_album,
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
                PROCESSING: [loc_prs.add_node_name(name="photos_q")],
                TRANSITIONS: {
                    ("what_is_next", "cur_photos"): cnd.regexp(r"\bwhat's\snext\b", re.I),
                    ("photos", "abbey_road"): int_cnd.is_yes_vars},
            },
            "abbey_road": {
                RESPONSE: """Here! It's the only original Beatles album cover to show neither the artist name nor """
                          """the album title. Do you remember the name of this album?""",
                PROCESSING: [loc_prs.add_misc_to_response, loc_prs.add_node_name(name="abbey_road")],
                TRANSITIONS: {
                    ("what_is_next", "cur_photos"): cnd.regexp(r"\bwhat's\snext\b", re.I),
                    ("photos", "fact_ar"): loc_cnd.has_correct_answer,
                    ("photos", "info_ar"): cnd.true
                },
                MISC: {"command": "goto", "objectId": "b9d08nbdvh8vsb"},
            },
            "fact_ar": {
                RESPONSE: """Yes, it's Abbey Road!! Did you know that after the album was released, the number plate """
                """"(LMW 281F) was repeatedly stolen from the white Volkswagen Beetle from the picture? Poor owner """
                """of the car...""",
                PROCESSING: [loc_prs.add_node_name(name="fact_ar")],
                TRANSITIONS: {
                    ("what_is_next", "cur_photos"): cnd.regexp(r"\bwhat's\snext\b", re.I),
                    ("photos", "yesterday&today"): cnd.true
                },
            },
            "info_ar": {
                RESPONSE: "It's Abbey Road! Photographer was given only 10 minutes to take the photo while he stood "
                          "on a step-ladder and a policeman held up traffic behind the camera. He took 6 photographs and "
                          "McCartney chose this one for the cover. ",
                PROCESSING: [loc_prs.add_node_name(name="info_ar")],
                TRANSITIONS: {
                    ("what_is_next", "cur_photos"): cnd.regexp(r"\bwhat's\snext\b", re.I),
                    ("photos", "yesterday&today"): cnd.true
                },
            },
            "yesterday&today": {
                RESPONSE: """This photo is from Whitaker photo session, where he assembled different scary props such """
                """as doll parts and trays of meat. One of the photos was used for the cover of Yesterday """
                """and Today album. We have some more photos of The Beatles, so be sure to check them out 🙂 """,
                PROCESSING: [loc_prs.add_misc_to_response],
                TRANSITIONS: {
                    ("what_is_next", "cur_last_photo"): cnd.regexp(r"\bwhat's\snext\b", re.I)
                },
                MISC: {"command": "goto", "objectId": "pv2qgzk51vmgq6"},
            },
        },
    },
    "song": {
        GRAPH: {
            "song_q": {
                RESPONSE: "All right, let's finish the albums here. What's your favorite Beatles song?",
                TRANSITIONS: {
                    ("what_is_next", "cur_songs"): cnd.regexp(r"\bwhat's\snext\b", re.I),
                    ("song", "fav_song"): loc_cnd.has_songs,
                    ("song", "why_song"): loc_cnd.is_beatles_song,
                    ("album", "who_beatle_1"): cnd.true
                },
            },
            "video_q": {
                RESPONSE: """What Beatles song do you like? We have "Hey Jude", "Don't Let Me Down", "We Can Work it Out",
                "Come Together", "Yellow Submarine", "Revolution", "Imagine", "Something", "Hello, Goodbye",
                "A Day In The Life", "Help" and "Penny Lane" here!""",
                TRANSITIONS: {
                    ("what_is_next", "cur_songs"): cnd.regexp(r"\bwhat's\snext\b", re.I),
                    ("song", "fav_song"): loc_cnd.has_songs,
                    ("song", "video_rep"): cnd.true},
            },
            "video_rep": {
                RESPONSE: """Unfortunately, we don't have this one here. You can choose from "Hey Jude", "Don't Let Me Down", 
                "We Can Work it Out", "Come Together", "Yellow Submarine", 
                "Revolution", "Imagine", "Something", "Hello, Goodbye", "A Day In The Life", "Help" and "Penny Lane"!""",
                TRANSITIONS: {
                    ("what_is_next", "cur_songs"): cnd.regexp(r"\bwhat's\snext\b", re.I),
                    ("song", "fav_song"): loc_cnd.has_songs,
                    trn.repeat(): cnd.true},
            },
            "fav_song": {
                RESPONSE: "Enjoy watching the music video! Just text me when you are done.",
                PROCESSING: [loc_prs.extract_song_id, loc_prs.add_misc_to_response],
                TRANSITIONS: {
                    ("what_is_next", "cur_songs"): cnd.regexp(r"\bwhat's\snext\b", re.I),
                    ("album", "who_beatle"): cnd.true,
                },
            },
            "why_song": {RESPONSE: "Why do you like this song?", TRANSITIONS: {("album", "who_beatle"): cnd.true}},
            "yellow_submarine": {
                RESPONSE: "Then let's watch a short video and after that you can watch the entire movie if you want! "
                          "Just let me know when you're done.",
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
            "fact_lennon": {
                RESPONSE: "I adore John Lennon! By the way, did you know that John Lennon’s father"
                " was absent for much of his early life but showed up when his son became famous?"
                " Sounds kind of sad... Let's take a look at his biography. Just text me when you're done :)",
                PROCESSING: [loc_prs.extract_members, loc_prs.fill_slots, loc_prs.add_misc_to_response],
                TRANSITIONS: {
                    ("what_is_next", "cur_band"): cnd.regexp(r"\bwhat's\snext\b", re.I),
                    ("beatles", "instruments_q"): cnd.true
                },
                MISC: {"command": "goto", "objectId": "w6mdvshkg95p4r"},
            },
            "fact_mccartney": {
                RESPONSE: "Paul McCartney is awesome! By the way, did you know that he played"
                " to what's believed to be the largest paid audience in recorded history? In 1989,"
                " he played a solo concert to a crowd of 350,000-plus in Brazil. That's amazing!"
                " Let's take a look at his biography. Just text me when you're done :)",
                PROCESSING: [loc_prs.extract_members, loc_prs.fill_slots, loc_prs.add_misc_to_response],
                TRANSITIONS: {
                    ("what_is_next", "cur_band"): cnd.regexp(r"\bwhat's\snext\b", re.I),
                    ("beatles", "instruments_q"): cnd.true
                },
                MISC: {"command": "goto", "objectId": "0fzh0phwszmzb1"},
            },
            "fact_harrison": {
                RESPONSE: "Oh, I love George Harrison! By the way, did you know that"
                " the song ‘CRACKERBOX PALACE’ is about his mansion? Modest as he was - he did live"
                " in a 120 room mansion on a 66 acre estate. Let's take a look at his biography. Just text me when you're done :)",
                PROCESSING: [loc_prs.extract_members, loc_prs.fill_slots, loc_prs.add_misc_to_response],
                TRANSITIONS: {
                    ("what_is_next", "cur_band"): cnd.regexp(r"\bwhat's\snext\b", re.I),
                    ("beatles", "instruments_q"): cnd.true
                },
                MISC: {"command": "goto", "objectId": "gg1cr8v40rv13x"},
            },
            "fact_starr": {
                RESPONSE: "Ringo is the best drummer in the world! By the way, did you know that due to his allergy"
                " he has never had pizza, curry, or onions? That didn’t stop him from doing a pizza"
                " commercial in 1995, though. Let's take a look at his biography. Just text me when you're done :)",
                PROCESSING: [loc_prs.extract_members, loc_prs.fill_slots, loc_prs.add_misc_to_response],
                TRANSITIONS: {
                    ("what_is_next", "cur_band"): cnd.regexp(r"\bwhat's\snext\b", re.I),
                    ("beatles", "instruments_q"): cnd.true
                },
                MISC: {"command": "goto", "objectId": "q07q698tfsb8hh"},
            },
        },
    },
    "instruments": {
        GRAPH: {
            "play_q": {
                RESPONSE: "And do you play any instrument?",
                PROCESSING: [loc_prs.add_node_name(name="play_q")],
                TRANSITIONS: {
                    ("what_is_next", "cur_instruments"): cnd.regexp(r"\bwhat's\snext\b", re.I),
                    ("instruments", "guitar_paul_1_2"): int_cnd.is_no_vars,
                    ("instruments", "guitar_paul_1"): cnd.true,
                },
            },
            "play_q_res": {
                RESPONSE: "What do you want to see: Paul's Zenith Model 17 acoustic, his Hofner 500/1 bass, "
                          "John's Rickenbacker 325 or Ringo's drum kit?",
                PROCESSING: [loc_prs.add_node_name(name="play_q_res")],
                TRANSITIONS: {
                    ("instruments", "guitar_paul_1"): loc_cnd.has_member(member_name=["zenith", "model", "acoustic"]),
                    ("instruments", "guitar_paul_2"): loc_cnd.has_member(member_name=["hofner", "500/1", "bass"]),
                    ("instruments", "guitar_lennon"): loc_cnd.has_member(member_name=["rickenbacker", "john's"]),
                    ("instruments", "drum_kit"): loc_cnd.has_member(member_name=["drumkit", "drum", "ringo"]),
                    ("what_is_next", "cur_instruments"): cnd.regexp(r"\bwhat's\snext\b", re.I),
                    trn.repeat(): cnd.true
                },
            },
            "guitar_paul_1": {
                RESPONSE: "{instrument_intro}"
                "In 1956, McCartney's father gave him a trumpet for his birthday. "
                """But, as Paul said later, "you couldn't sing with a trumpet stuck in your mouth", """
                "so he traded it for Zenith Model 17 acoustic. Let's have a look at it. "
                "Isn't it beautiful?",
                PROCESSING: [loc_prs.extract_inst, loc_prs.fill_slots, loc_prs.add_misc_to_response, loc_prs.add_node_name(name="play_q_res")],
                TRANSITIONS: {
                    ("what_is_next", "cur_instruments"): cnd.regexp(r"\bwhat's\snext\b", re.I),
                    ("instruments", "guitar_paul_2"): cnd.true
                },
                MISC: {"command": "goto", "objectId": "f47z2rzm0tt4b8"},
            },
            "guitar_paul_1_2": {
                RESPONSE: "I can show you Paul McCartney's guitar! "
                "In 1956, McCartney's father gave him a trumpet for his birthday. "
                """But, as Paul said later, "you couldn't sing with a trumpet stuck in your mouth", """
                "so he traded it for Zenith Model 17 acoustic. Let's have a look at it. "
                "Isn't it beautiful?",
                PROCESSING: [loc_prs.add_misc_to_response],
                TRANSITIONS: {
                    ("what_is_next", "cur_instruments"): cnd.regexp(r"\bwhat's\snext\b", re.I),
                    ("instruments", "guitar_paul_2"): cnd.true
                },
                MISC: {"command": "goto", "objectId": "f47z2rzm0tt4b8"},
            },
            "guitar_paul_2": {
                RESPONSE: "Here is Paul's Hofner 500/1 bass. "
                """He went with this Hofner from "I Want to Hold Your Hand" through "Let It Be" and beyond. """
                "Do you want to take a look at one of John Lennon's guitars?",
                PROCESSING: [loc_prs.add_misc_to_response, loc_prs.add_node_name(name="guitar_paul_2")],
                TRANSITIONS: {
                    ("what_is_next", "cur_instruments"): cnd.regexp(r"\bwhat's\snext\b", re.I),
                    ("instruments", "guitar_lennon"): int_cnd.is_yes_vars,
                    ("photos", "photos_q"): cnd.true
                },
                MISC: {"command": "goto", "objectId": "r369t7g5cw3x0h"},
            },
            "guitar_lennon": {
                RESPONSE: "Look! It's Lennon's Rickenbacker 325! He had four models of this guitar. Do you like it?",
                PROCESSING: [loc_prs.add_misc_to_response, loc_prs.add_node_name(name="guitar_lennon")],
                TRANSITIONS: {
                    ("what_is_next", "cur_instruments"): cnd.regexp(r"\bwhat's\snext\b", re.I),
                    ("instruments", "drum_kit"): cnd.true
                },
                MISC: {"command": "goto", "objectId": "07ptwckzth85qz"},
            },
            "drum_kit": {
                RESPONSE: "It is Ringo Starr's drum kit. During his time in The Beatles, he played six different drum kits, "
                "five of which were from Ludwig.",
                PROCESSING: [loc_prs.add_misc_to_response],
                TRANSITIONS: {
                    ("photos", "photos_q"): cnd.true},
                MISC: {"command": "goto", "objectId": "vx6bwczc94mtpq"},
            },
        },
    },
    'what_is_next': {
        GRAPH: {
            "cur_album": {
                RESPONSE: "We can continue looking at the albums or we can move on to songs. What would you prefer?",
                TRANSITIONS: {
                ("song", "song_q"): cnd.regexp(r"\b(move)|(songs)\b", re.I),
                ("album", "please_please_me"): cnd.all([loc_cnd.is_next(album_name="what_album"), cnd.regexp(r"\b(continue)|(albums)\b", re.I)]),
                ("album", "please_please_me"): cnd.all([loc_cnd.is_next(album_name="Let It Be"), cnd.regexp(r"\b(continue)|(albums)\b", re.I)]),
                ("album", "with_the_beatles"): cnd.all([loc_cnd.is_next(album_name="Please Please Me"), cnd.regexp(r"\b(continue)|(albums)\b", re.I)]),
                ("album", "a_hard_days_night_wrong"): cnd.all([loc_cnd.is_next(album_name="With The Beatles"), cnd.regexp(r"\b(continue)|(albums)\b", re.I)]),
                ("album", "beatles_for_sale"): cnd.all([loc_cnd.is_next(album_name="Hard Day's Night"), cnd.regexp(r"\b(continue)|(albums)\b", re.I)]),
                ("album", "help"): cnd.all([loc_cnd.is_next(album_name="Beatles For Sale"), cnd.regexp(r"\b(continue)|(albums)\b", re.I)]),
                ("album", "rubber_soul"): cnd.all([loc_cnd.is_next(album_name="Help"), cnd.regexp(r"\b(continue)|(albums)\b", re.I)]),
                ("album", "revolver"): cnd.all([loc_cnd.is_next(album_name="Rubber Soul"), cnd.regexp(r"\b(continue)|(albums)\b", re.I)]),
                ("album", "yellow_submarine"): cnd.all([loc_cnd.is_next(album_name="Revolver"), cnd.regexp(r"\b(continue)|(albums)\b", re.I)]),
                ("album", "sgt_peppers"): cnd.all([loc_cnd.is_next(album_name="Yellow Submarine"), cnd.regexp(r"\b(continue)|(albums)\b", re.I)]),
                ("album", "white_album"): cnd.all([loc_cnd.is_next(album_name="Sgt. Pepper's Lonely Hearts Club Band"), cnd.regexp(r"\b(continue)|(albums)\b", re.I)]),
                ("album", "abbey_road"): cnd.all([loc_cnd.is_next(album_name="White Album"), cnd.regexp(r"\b(continue)|(albums)\b", re.I)]),
                ("album", "let_it_be"): cnd.all([loc_cnd.is_next(album_name="Abbey Road"), cnd.regexp(r"\b(continue)|(albums)\b", re.I)]),
                },
            },
            "cur_history": {
                RESPONSE: "We can continue speaking about the history of the band or we can move on to albums."
                          " What would you prefer?",
                TRANSITIONS: {
                    ("album", "what_album"): cnd.regexp(r"\b(move)|(albums)\b", re.I),
                    ("history", "first_members_res"): cnd.regexp(r"\b(continue)|(history)\b", re.I),
                },
            },
            "cur_songs": {
                RESPONSE: "We can continue looking at the songs or we can move on to the band. What would you prefer?",
                TRANSITIONS: {
                    ("song", "video_q"): cnd.regexp(r"\b(continue)|(songs)\b", re.I),
                    ("album", "who_beatle_res"): cnd.regexp(r"\b(move)|(band)|(beatles)\b", re.I)
                },
            },
            "cur_band": {
                RESPONSE: "We can continue looking at the band or we can move on to instruments. What would you prefer?",
                TRANSITIONS: {
                    ("album", "who_beatle_res"): cnd.regexp(r"\b(continue)|(band)|(beatles)\b", re.I),
                    ("instruments", "play_q"): cnd.regexp(r"\b(move)|(instruments)\b", re.I)
                },
            },
            "cur_instruments": {
                RESPONSE: "We can continue looking at the instruments or we can move on to photos. What would you prefer?",
                TRANSITIONS: {
                    ("photos", "abbey_road"): cnd.regexp(r"\b(move)|(photos)|\b", re.I),
                    ("instruments", "guitar_paul_2"): cnd.all([loc_cnd.is_next(album_name="guitar_paul_1"), cnd.regexp(r"\b(continue)|(instruments)\b", re.I)]),
                    ("instruments", "guitar_lennon"): cnd.all([loc_cnd.is_next(album_name="guitar_paul_2"), cnd.regexp(r"\b(continue)|(instruments)\b", re.I)]),
                    ("instruments", "drum_kit"): cnd.all([loc_cnd.is_next(album_name="guitar_lennon"), cnd.regexp(r"\b(continue)|(instruments)\b", re.I)]),
                    ("instruments", "play_q_res"): cnd.regexp(r"\b(continue)|(instruments)|\b", re.I),
                }
            },
            "cur_photos": {
                RESPONSE: "We can continue looking at the photos or we can finish. What would you prefer?",
                TRANSITIONS: {
                    ("photos", "abbey_road", 1): cnd.all([loc_cnd.is_next(album_name="photos_q"), cnd.regexp(r"\b(continue)|(photos)\b", re.I)]),
                    ("photos", "yesterday&today", 0.9): cnd.all([loc_cnd.is_next(album_name="abbey_road"), cnd.regexp(r"\b(continue)|(photos)\b", re.I)]),
                    ("photos", "yesterday&today", 0.8): cnd.all([loc_cnd.is_next(album_name="fact_ar"), cnd.regexp(r"\b(continue)|(photos)\b", re.I)]),
                    ("photos", "yesterday&today", 0.7): cnd.all([loc_cnd.is_next(album_name="info_ar"), cnd.regexp(r"\b(continue)|(photos)\b", re.I)])
                }
            },
            "cur_last_photo": {
                RESPONSE: "Let's finish looking at the photos here. Feel free to walk around and do not hesitate"
                          " to ask me questions about albums, musical instruments, or the artists themselves."
                          " I'm happy to help!"
            }
        }
    },
}


actor = Actor(flows, start_node_label=("beatles", "start"), default_transition_priority=1.0,)
