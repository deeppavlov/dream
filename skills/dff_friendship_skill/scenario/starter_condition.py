from df_engine.core import Actor, Context

import common.dff.integration.context as int_ctx
import common.dff.integration.condition as int_cnd


def genre_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    shared_memory = int_ctx.get_shared_memory(ctx, actor)
    greeting_type = shared_memory.get("greeting_type", "")
    flag = greeting_type == "starter_genre"
    return flag


def weekday_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    shared_memory = int_ctx.get_shared_memory(ctx, actor)
    greeting_type = shared_memory.get("greeting_type", "")
    flag = greeting_type == "starter_weekday"
    return flag


def positive_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    no_requests = int_cnd.no_requests(ctx, actor)
    sentiment = int_ctx.get_human_sentiment(ctx, actor)
    flag = all([no_requests, sentiment == "positive", genre_condition(ctx, actor)])
    return flag


def negative_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    no_requests = int_cnd.no_requests(ctx, actor)
    sentiment = int_ctx.get_human_sentiment(ctx, actor)
    flag = all([no_requests, sentiment == "negative", genre_condition(ctx, actor)])
    return flag


def neutral_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    no_requests = int_cnd.no_requests(ctx, actor)
    sentiment = int_ctx.get_human_sentiment(ctx, actor)
    flag = all([no_requests, sentiment == "neutral", genre_condition(ctx, actor)])
    return flag


def friday_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    flag = all([int_cnd.no_requests(ctx, actor), weekday_condition(ctx, actor)])
    return flag


def reason_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    flag = int_cnd.no_requests(ctx, actor)
    return flag


def smth_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    flag = int_cnd.no_requests(ctx, actor)
    return flag


def starter_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    shared_memory = int_ctx.get_shared_memory(ctx, actor)
    greeting_type = shared_memory.get("greeting_type", "")
    flag = int_cnd.no_requests(ctx, actor) and (greeting_type in ["starter_genre", "starter_weekday"])
    return flag
