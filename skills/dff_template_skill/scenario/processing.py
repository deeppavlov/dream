import logging
import re
import json

from dff.core import Node, Context, Actor


logger = logging.getLogger(__name__)
# ....


def extract_members(node_label: str, node: Node, ctx: Context, actor: Actor, *args, **kwargs):
    slots = ctx.misc.get("slots", {})
    members = ["John Lennon", "Ringo Starr", "Paul McCartney", "George Harrison"]

    members_re = "|".join(members)
    extracted_member = re.findall(members_re, ctx.last_request, re.IGNORECASE)
    if extracted_member:
        slots["beatles_member"] = extracted_member[0]
        ctx.misc["slots"] = slots

    return node_label, node


def extract_inst(node_label: str, node: Node, ctx: Context, actor: Actor, *args, **kwargs):
    slots = ctx.misc.get("slots", {})
    insts = ["trumpet", "drums", "guitar"]
    insts_re = "|".join(insts)
    extracted_inst = re.findall(insts_re, ctx.last_request, re.IGNORECASE)
    if extracted_inst:
        slots[extracted_inst[0]] = extracted_inst[0]
        ctx.misc["slots"] = slots

    return node_label, node


def extract_albums(node_label: str, node: Node, ctx: Context, actor: Actor, *args, **kwargs):
    slots = ctx.misc.get("slots", {})
    albums = [
        "Please Please Me",
        "With the Beatles",
        "Introducing... The Beatles",
        "Meet the Beatles!",
        "Twist and Shout",
        "The Beatles' Second Album",
        "The Beatles' Long Tall Sally",
        "A Hard Day's Night",
        "Something New",
        "Help!",
        "Sgt. Pepper's Lonely Hearts Club Band",
        "White Album",
        "The Beatles Beat",
        "Another Beatles Christmas Record",
        "Beatles '65",
        "Beatles VI",
        "Five Nights In A Judo Arena",
        "The Beatles at the Hollywood Bowl",
        "Live! at the Star-Club in Hamburg, German; 1962",
        "The Black Album",
        "20 Exitos De Oro",
        "A Doll's House",
        "The Complete Silver Beatles",
        "Rock 'n' Roll Music Vol. 1",
        "Yellow Submarine",
        "Let It Be",
        "Beatles for Sale",
        "Revolver",
        "Abbey Road",
        "Rubber Soul",
    ]

    albums_re = "|".join(albums)
    extracted_album = re.findall(albums_re, ctx.last_request, re.IGNORECASE)
    if extracted_album:
        slots["album_name"] = extracted_album[0]
        ctx.misc["slots"] = slots

    return node_label, node


def slot_filling_albums(node_label: str, node: Node, ctx: Context, actor: Actor, *args, **kwargs):
    slots = ctx.misc.get("slots", {})
    slots["first_album"] = (
        "Let's begin our trip here. I will show you some albums first. " "If you get tired, just text me 'MOVE ON'"
    )
    slots["a_hard_days_night_corr"] = "And you're right, A Hard Day's Night it was! "
    slots["a_hard_days_noght_wrong"] = "It was Hard Day's Night!"
    slots["rubber_soul"] = "However, it was after this cry for 'Help' that the Beatles became the Beatles."
    slots["yellow_submarine"] = "Then let's take a look at the album."
    slots["abbey_road"] = (
        "By the way, The White Album' recording sessions lasted 137 days! Abbey Road, on the opposite,"
        "was recorded in one 12-hour session -- even faster than Please Please Me! "
    )
    slots["let_it_be"] = (
        "Did you know that Abbey Road was created and issued after the recording of the Beatles' "
        "last released album took place?"
    )

    for slot_name, slot_value in slots.items():
        node.response = node.response.replace("{" f"{slot_name}" "}", slot_value)
    return node_label, node


def fill_slots(node_label: str, node: Node, ctx: Context, actor: Actor, *args, **kwargs):
    for slot_name, slot_value in ctx.misc.get("slots", {}).items():
        node.response = node.response.replace("{" f"{slot_name}" "}", slot_value)
    return node_label, node


def extract_song_id(ctx: Context, actor: Actor, *args, **kwargs):
    songs = [
        "Hey Jude",
        "Don't Let Me Down",
        "We Can Work it Out",
        "Come Together",
        "Yellow Submarine",
        "Revolution",
        "Imagine",
        "Something",
        "Hello, Goodbye",
        "A Day In The Life",
        "Help!",
        "Penny Lane",
    ]

    songs_ids = {
        "Hey Jude": "826kt29479qp27",
        "Don't Let Me Down": "hvnck9pvgnpft4",
        "We Can Work it Out": "s1mfzw528vt05m",
        "Come Together": "qrg1tn7dpx2066",
        "Yellow Submarine": "bsqcc0bkbkxb75",
        "Revolution": "grmx7c4g9rb412",
        "Imagine": "rh8bfh6m7fr13g",
        "Something": "74v09tbmqmbf9z",
        "Hello, Goodbye": "87krd594czgd2d",
        "A Day In The Life": "b8ptdvbm1rzccs",
        "Help!": "zk3dvf2qt7sr0p",
        "Penny Lane": "zhw7593t9mb9gn",
    }

    songs_re = "|".join(songs)
    extracted_song = re.findall(songs_re, ctx.last_request, re.IGNORECASE)
    if extracted_song:
        for k in songs_ids.keys():
            if extracted_song[0].lower() == k.lower():
                id = songs_ids[k]

    return id


def add_misc_to_response(node_label: str, node: Node, ctx: Context, actor: Actor, *args, **kwargs):
    node.response = f"{node.response} {json.dumps(node.misc)}"
    return node_label, node
