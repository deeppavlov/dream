import re

from df_engine.core import Actor, Context

import common.dff.integration.context as int_ctx
import common.greeting as common_greeting
import common.link as common_link
import common.universal_templates as common_universal_templates
import common.utils as common_utils
from common.scenarios.games import was_game_mentioned


GREETING_STEPS = list(common_greeting.GREETING_QUESTIONS)
link_to_skill2key_words = {
    skill_name: common_link.link_to_skill2key_words[skill_name]
    for skill_name in common_link.link_to_skill2key_words
    if skill_name in common_link.SKILLS_FOR_LINKING
}

link_to_skill2i_like_to_talk = {
    skill_name: common_link.link_to_skill2i_like_to_talk[skill_name]
    for skill_name in common_link.link_to_skill2i_like_to_talk
    if skill_name in common_link.SKILLS_FOR_LINKING
}

patterns_bot = ["chat about", "talk about", "on your mind"]
re_patterns_bot = re.compile(common_utils.join_words_in_or_pattern(patterns_bot), re.IGNORECASE)

patterns_human = ["no idea", "don't know", "nothing", "anything", "your favorite topic"]
re_patterns_human = re.compile(common_utils.join_words_in_or_pattern(patterns_human), re.IGNORECASE)

patterns_human = ["clean", "tide", "reorganize", "tidi", "laundry"]
cleaned_up_patterns_re = re.compile(common_utils.join_words_in_or_pattern(patterns_human), re.IGNORECASE)

patterns_human_1 = ["movie", "tv", "netflix", "hulu", "disney", "hbo", "cbs", "paramount"]
watched_film_patterns_1_re = re.compile(common_utils.join_words_in_or_pattern(patterns_human_1), re.IGNORECASE)

patterns_human_2 = ["watched", "seen", "saw", "enjoyed", "binged"]
watched_film_patterns_2_re = re.compile(common_utils.join_words_in_or_pattern(patterns_human_2), re.IGNORECASE)

patterns_human_1 = ["book", "story", "article", "magazine"]
read_book_patterns_1_re = re.compile(common_utils.join_words_in_or_pattern(patterns_human_1), re.IGNORECASE)

patterns_human_2 = ["read", "enjoy", "looked through", "wade", "flicked"]
read_book_patterns_2_re = re.compile(common_utils.join_words_in_or_pattern(patterns_human_2), re.IGNORECASE)

patterns_human_1 = ["game", "computergame", "videogame", "xbox", "x box", "playstation", "play station", "nintendo"]
played_computer_game_patterns_1_re = re.compile(common_utils.join_words_in_or_pattern(patterns_human_1), re.IGNORECASE)

patterns_human_2 = ["play", "enjoy"]
played_computer_game_patterns_2_re = re.compile(common_utils.join_words_in_or_pattern(patterns_human_2), re.IGNORECASE)


def std_weekend_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    human_text = int_ctx.get_last_human_utterance(ctx, actor)["text"]

    prev_was_about_topic = common_universal_templates.if_utterance_requests_topic(
        int_ctx.get_last_bot_utterance(ctx, actor)
    )
    anything = re.search(re_patterns_human, human_text)

    flag = bool(prev_was_about_topic and anything)

    return flag


def sys_cleaned_up_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    human_text = int_ctx.get_last_human_utterance(ctx, actor)["text"]

    flag = bool(re.search(cleaned_up_patterns_re, human_text))
    return flag


def sys_slept_in_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    human_text = int_ctx.get_last_human_utterance(ctx, actor)["text"]

    flag = "slept" in human_text
    return flag


def sys_feel_great_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    human_utterance = int_ctx.get_last_human_utterance(ctx, actor)

    flag = common_utils.is_no(human_utterance)
    return flag


def sys_need_more_time_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    human_utterance = int_ctx.get_last_human_utterance(ctx, actor)
    flag = common_utils.is_no(human_utterance)
    return flag


def sys_watched_film_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    human_text = int_ctx.get_last_human_utterance(ctx, actor)["text"]
    flag = bool(re.search(watched_film_patterns_1_re, human_text) and re.search(watched_film_patterns_2_re, human_text))
    return flag


def sys_read_book_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    human_text = int_ctx.get_last_human_utterance(ctx, actor)["text"]
    flag = bool(re.search(read_book_patterns_1_re, human_text) and re.search(read_book_patterns_2_re, human_text))
    return flag


def sys_played_computer_game_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    human_text = int_ctx.get_last_human_utterance(ctx, actor)["text"]
    flag = bool(
        re.search(played_computer_game_patterns_1_re, human_text)
        and re.search(played_computer_game_patterns_2_re, human_text)
    )
    return flag


def sys_play_on_weekends_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    human_utterance = int_ctx.get_last_human_utterance(ctx, actor)

    flag = bool(was_game_mentioned(human_utterance))
    return flag


def sys_play_regularly_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    human_utterance = int_ctx.get_last_human_utterance(ctx, actor)

    flag = common_utils.is_yes(human_utterance)
    return flag


def sys_play_once_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    human_utterance = int_ctx.get_last_human_utterance(ctx, actor)

    flag = common_utils.is_no(human_utterance)
    return flag
