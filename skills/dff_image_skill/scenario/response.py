import logging
import random
from df_engine.core import Context, Actor
import common.dff.integration.context as int_ctx
import scenario.processing as loc_prs

logger = logging.getLogger(__name__)

DEFAULT_RESPONSE = "Okay. Why did you send me this picture?"


def animals_response(ctx: Context, actor: Actor, excluded_skills=None, *args, **kwargs) -> str:
    caption = (
        int_ctx.get_last_human_utterance(ctx, actor)
        .get("annotations", {})
        .get("image_captioning", {})
        .get("caption", "")
    )
    if caption != "" and caption is not None:
        animal = loc_prs.extract_entity(caption, loc_prs.get_all_possible_entities("animal"))
        if animal != "" and animal is not None:
            int_ctx.set_confidence(ctx, actor, 1.0)
            response = random.choice(
                [
                    "What a muzzle! Would you like to have an animal like that?",
                    "I would like to have an animal like that. I wonder if it eats a lot.",
                    f"Is it your {animal}?",
                ]
            )
        else:
            int_ctx.set_confidence(ctx, actor, 0.85)
            response = DEFAULT_RESPONSE
    else:
        int_ctx.set_confidence(ctx, actor, 0.85)
        response = DEFAULT_RESPONSE
    logger.info(f"dff-image-skill animals response: {response}")
    return response


def food_response(ctx: Context, actor: Actor, excluded_skills=None, *args, **kwargs) -> str:
    caption = (
        int_ctx.get_last_human_utterance(ctx, actor)
        .get("annotations", {})
        .get("image_captioning", {})
        .get("caption", "")
    )
    if caption != "" and caption is not None:
        food = loc_prs.extract_entity(caption, loc_prs.get_all_possible_entities("food"))
        if food != "" and food is not None:
            int_ctx.set_confidence(ctx, actor, 0.85)
            response = random.choice(
                [
                    f"Did you cook this {food} by yourself? It looks delicious!",
                    f"Would you like to eat this {food}?",
                ]
            )
        else:
            int_ctx.set_confidence(ctx, actor, 0.85)
            response = DEFAULT_RESPONSE
    else:
        int_ctx.set_confidence(ctx, actor, 0.85)
        response = DEFAULT_RESPONSE
    logger.info(f"dff-image-skill food response: {response}")
    return response


def people_response(ctx: Context, actor: Actor, excluded_skills=None, *args, **kwargs) -> str:
    caption = (
        int_ctx.get_last_human_utterance(ctx, actor)
        .get("annotations", {})
        .get("image_captioning", {})
        .get("caption", "")
    )
    if caption != "" and caption is not None:
        verb = loc_prs.extract_verb_from_sentence(caption)
        if verb != "" and verb is not None:
            int_ctx.set_confidence(ctx, actor, 1.0)
            response = f"Do you enjoy {verb} with other people?"
        else:
            int_ctx.set_confidence(ctx, actor, 0.85)
            response = DEFAULT_RESPONSE
    else:
        int_ctx.set_confidence(ctx, actor, 0.85)
        response = DEFAULT_RESPONSE
    logger.info(f"dff-image-skill people response: {response}")
    return response


def generic_response(ctx: Context, actor: Actor, excluded_skills=None, *args, **kwargs) -> str:
    caption = (
        int_ctx.get_last_human_utterance(ctx, actor)
        .get("annotations", {})
        .get("image_captioning", {})
        .get("caption", "")
    )
    if caption != "" and caption is not None:
        int_ctx.set_confidence(ctx, actor, 1.0)
        response = random.choice(
            [
                f"Cool! Why did you send me {caption}?",
                f"It looks interesting, what did you mean by sending me {caption}?",
            ]
        )
    else:
        int_ctx.set_confidence(ctx, actor, 0.85)
        response = DEFAULT_RESPONSE
    logger.info(f"dff-image-skill generic response: {response}")
    return response
