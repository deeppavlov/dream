import logging
import re

from dff.core import Context, Actor


logger = logging.getLogger(__name__)
# ....


def has_album(album_name: str):
    def has_album_condition(ctx: Context, actor: Actor, *args, **kwargs):
        return bool(re.findall(album_name, ctx.last_request, re.IGNORECASE))

    return has_album_condition


def not_visited_album(ctx: Context, actor: Actor, *args, **kwargs):
    ctx.misc["counter"] = ctx.misc.get("counter", 0) + 1
    return ctx.misc["counter"] != 12


def move_on(ctx: Context, actor: Actor, *args, **kwargs):
    return bool(re.findall("move on", ctx.last_request, re.IGNORECASE))


def has_songs(ctx: Context, actor: Actor, *args, **kwargs):
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

    songs_re = "|".join(songs)
    return bool(re.findall(songs_re, ctx.last_request, re.IGNORECASE))


def has_member(member_name: str):
    def has_membar_condition(ctx: Context, actor: Actor, *args, **kwargs):
        return bool(re.findall(member_name, ctx.last_request, re.IGNORECASE))

    return has_membar_condition


def has_correct_answer(ctx: Context, actor: Actor, *args, **kwargs):
    a = ["Abbey Road", "A Hard Day's Night"]
    ar = "|".join(a)
    return bool(re.findall(ar, ctx.last_request, re.IGNORECASE))


def has_any_album(ctx: Context, actor: Actor, *args, **kwargs):
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
    return bool(re.findall(albums_re, ctx.last_request, re.IGNORECASE))
