import logging
import re
import json
from . import condition as loc_cnd
from dff.core import Node, Context, Actor


logger = logging.getLogger(__name__)
# ....


def extract_members(node_label: str, node: Node, ctx: Context, actor: Actor, *args, **kwargs):
    slots = ctx.misc.get("slots", {})
    members = ["John", "Len*on", "Ringo", "Star*", "Paul", "McCartn*y", "George", "Har*ison"]
    members_re = "|".join(members)
    extracted_member = re.findall(members_re, ctx.last_request, re.IGNORECASE)
    if re.findall(r'john|len*on', ctx.last_request, re.IGNORECASE) != []:
        slots["beatles_member"] = "John Lennon"
        ctx.misc["slots"] = slots
    elif re.findall(r'paul|mccartne*y', ctx.last_request, re.IGNORECASE) != []:
        slots["beatles_member"] = "Paul McCartney"
        ctx.misc["slots"] = slots
    elif re.findall(r'ringo|star*s*', ctx.last_request, re.IGNORECASE) != []:
        slots["beatles_member"] = "Ringo Starr"
        ctx.misc["slots"] = slots
    elif re.findall(r'george|har*ison', ctx.last_request, re.IGNORECASE) != []:
        slots["beatles_member"] = "George Harrison"
        ctx.misc["slots"] = slots

    return node_label, node


def extract_inst(node_label: str, node: Node, ctx: Context, actor: Actor, *args, **kwargs):
    slots = ctx.misc.get("slots", {})
    insts = ["trumpet", "drums", "guitar", "accordion", "bagpipe", "banjo", "bugle", "cello", "clarinet", "cymbal", 
             "flute", "horn", "harmonica", "harp", "keyboard", "maracase", "organ", "flute", "piano", "recorder",
             "saxophone", "sitar", "tambourine", "triangle", "trombone", "tuba", "ukulele", "violin", 
             "xylophone", "bassoon", "castanet", "didgeridoo", "gong", "harpsichord", "lute", "mandolin", "oboe", 
             "piccolo", "viola"]
    extracted_inst = loc_cnd.levenshtein_cand(insts, ctx.last_request)
    if "guitar" in extracted_inst[1]:
        slots["instrument_intro"] = "Cool! We have a lot of guitars here. Let's begin with a story about Paul McCartney's first guitar. "
        ctx.misc["slots"] = slots
    elif "trumpet" in extracted_inst[1]:
        slots["instrument_intro"] = "Then I have a funny story about trumpets for you! "
        ctx.misc["slots"] = slots
    elif "drums" in extracted_inst[1]:
        slots["instrument_intro"] = "If you like drums, you must like Ringo Starr! Let's save his his drumkit for last and begin with the guitars. "
        ctx.misc["slots"] = slots
    elif extracted_inst[0]:
        slots["instrument_intro"] = f"That's so cool! We don't have {extracted_inst[1]}s here, but I can show you some other instruments. "
        ctx.misc["slots"] = slots
    else:
        slots["instrument_intro"] = "All right, let me show you instruments that we have here! "
        ctx.misc["slots"] = slots
    return node_label, node


def extract_albums(node_label: str, node: Node, ctx: Context, actor: Actor, *args, **kwargs):
    slots = ctx.misc.get("slots", {})
    albums = [
        "Please Please Me",
        "With the Beatles",
        "A Hard Day's Night",
        "Help!",
        "Sgt. Pepper's Lonely Hearts Club Band",
        "White Album",
        "Yellow Submarine",
        "Let It Be",
        "Beatles for Sale",
        "Revolver",
        "Abbey Road",
        "Rubber Soul"
    ]
    extracted_album = loc_cnd.levenshtein_item(albums, ctx.last_request)
    if extracted_album:
        slots["album_name"] = extracted_album
        ctx.misc["slots"] = slots

    return node_label, node


def slot_filling_albums(node_label: str, node: Node, ctx: Context, actor: Actor, *args, **kwargs):
    slots = ctx.misc.get("slots", {})
    slots["sgt_peppers"] = "George Martin played a significant role in recording most of the band’s albums, including their arguably greatest success — Sgt Pepper’s Lonely Hearts Club Band."
    slots["a_hard_days_night_corr"] = "And you're right, A Hard Day's Night it was! "
    slots["a_hard_days_night_wrong"] = "It was A Hard Day's Night! "
    slots["rubber_soul"] = "However, it was after this cry for 'Help!' that the Beatles became the Beatles. "
    slots["yellow_submarine"] = "Then let's take a look at the album. "
    slots["abbey_road"] = "By the way, The White Album' recording sessions lasted 137 days! And Abbey Road was recorded in 12 hours. "
    slots["let_it_be"] = (
        "Did you know that Abbey Road was created and issued after the recording of the Beatles' "
        "last released album took place? "
    )
    slots["first_album"] = "Let's begin our trip here! If you get tired, just say 'move on'. "
    for slot_name, slot_value in slots.items():
        if re.search(r"((.*i\swant\sto\ssee\s)|(.*i\swanna\ssee\s)|(.*\slook\sat\s)|"
                     r"(.*show\sme\s)|(.*tell\sme\s)|(.*go\sto\s))(?P<item>.*)", ctx.last_request, re.I):
            slot_value = ""
        elif ctx.misc.get("first_album") is None and slot_name != "first_album":
            slot_value = ""
        elif ctx.misc.get("first_album") is None and slot_name == "first_album":
            ctx.misc["first_album"] = True
        elif ctx.misc.get("first_album") is not None:
            if ctx.misc["first_album"] == True and slot_name == "first_album":
                slot_value = ""
        node.response = node.response.replace("{" f"{slot_name}" "}", slot_value)

    return node_label, node


def extract_song_id(node_label: str, node: Node, ctx: Context, actor: Actor, *args, **kwargs):
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
        "Help",
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
        "Help": "zk3dvf2qt7sr0p",
        "Penny Lane": "zhw7593t9mb9gn",
    }

    songs_re = "|".join(songs)
    extracted_song = re.findall(songs_re, ctx.last_request, re.IGNORECASE)
    song_id = -1
    if extracted_song:
        for k in songs_ids.keys():
            if extracted_song[0].lower() == k.lower():
                song_id = songs_ids[k]

    node.misc = {"command": "goto", "objectId": song_id}

    return node_label, node


def fill_slots(node_label: str, node: Node, ctx: Context, actor: Actor, *args, **kwargs):
    for slot_name, slot_value in ctx.misc.get("slots", {}).items():
        node.response = node.response.replace("{" f"{slot_name}" "}", slot_value)
    return node_label, node


def increment_album_counter(node_label: str, node: Node, ctx: Context, actor: Actor, *args, **kwargs):
    ctx.misc["album_counter"] = ctx.misc.get("album_counter", 0) + 1
    return node_label, node


def add_misc_to_response(node_label: str, node: Node, ctx: Context, actor: Actor, *args, **kwargs):
    node.response = f"{node.response} {json.dumps(node.misc)}"
    return node_label, node



def extract_members_id(node_label: str, node: Node, ctx: Context, actor: Actor, *args, **kwargs):
    members = [
        "Paul McCartney",
        "Ringo Starr",
        "John Lennon",
        "George Harrison",
        "Paul",
        "McCartney",
        "Ringo",
        "Starr",
        "John",
        "Lennon",
        "George",
        "Harrison"
    ]

    members_ids = {
        "Paul McCartney": "0fzh0phwszmzb1",
        "Ringo Starr" : "q07q698tfsb8hh",
        "John Lennon": "w6mdvshkg95p4r",
        "George Harrison": "gg1cr8v40rv13x",
        "Paul": "0fzh0phwszmzb1",
        "McCartney": "0fzh0phwszmzb1",
        "Ringo": "q07q698tfsb8hh",
        "Starr": "q07q698tfsb8hh",
        "John": "w6mdvshkg95p4r",
        "Lennon": "w6mdvshkg95p4r",
        "George": "gg1cr8v40rv13x",
        "Harrison": "gg1cr8v40rv13x"
    }

    members_re = "|".join(members)
    extracted_member = re.findall(members_re, ctx.last_request, re.IGNORECASE)
    if extracted_member:
        for k in members_ids.keys():
            if extracted_member[0].lower() == k.lower():
                id = members_ids[k]

    node.misc = {"command": "goto", "objectId": id}

    return node_label, node


def add_node_name(name: str):
    def node_name(node_label: str, node: Node, ctx: Context, actor: Actor, *args, **kwargs):
        ctx.misc["current_node"] = name
        return node_label, node
    return node_name
