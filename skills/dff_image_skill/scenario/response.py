import logging
import random
from df_engine.core import Context, Actor
import common.dff.integration.context as int_ctx
import scenario.processing as loc_prs

logger = logging.getLogger(__name__)


def animals_response(ctx: Context, actor: Actor, excluded_skills=None, *args, **kwargs) -> str:
    caption = (
        int_ctx.get_last_human_utterance(ctx, actor)
        .get("annotations", {})
        .get("image_captioning", {})
        .get("caption", {})
    )
    animal = loc_prs.extract_entity(str(caption), loc_prs.get_all_possible_entities("animal"))
    responses = [
        "What a muzzle! Would you like to have an animal like that?",
        "I would like to have an animal like that. I wonder if it eats a lot.",
        f"Is it your {animal}?",
    ]
    int_ctx.set_confidence(ctx, actor, 0.85)
    return random.choice(responses)


def food_response(ctx: Context, actor: Actor, excluded_skills=None, *args, **kwargs) -> str:
    caption = (
        int_ctx.get_last_human_utterance(ctx, actor)
        .get("annotations", {})
        .get("image_captioning", {})
        .get("caption", {})
    )
    food = loc_prs.extract_entity(str(caption), loc_prs.get_all_possible_entities("food"))
    responses = [
        f"Did you cook this {food} by yourself? It looks delicious!",
        f"Would you like to eat this {food}?",
    ]
    int_ctx.set_confidence(ctx, actor, 0.85)
    return random.choice(responses)


def people_response(ctx: Context, actor: Actor, excluded_skills=None, *args, **kwargs) -> str:
    caption = (
        int_ctx.get_last_human_utterance(ctx, actor)
        .get("annotations", {})
        .get("image_captioning", {})
        .get("caption", {})
    )
    verb = loc_prs.extract_verb_from_sentence(str(caption))
    int_ctx.set_confidence(ctx, actor, 0.85)
    return f"Do you enjoy {verb} with other people?"


def generic_response(ctx: Context, actor: Actor, excluded_skills=None, *args, **kwargs) -> str:
    caption = (
        int_ctx.get_last_human_utterance(ctx, actor)
        .get("annotations", {})
        .get("image_captioning", {})
        .get("caption", {})
    )
    int_ctx.set_confidence(ctx, actor, 0.85)
    return random.choice(
        [
            f"Cool! Why did you send me {str(caption)}?",
            f"It looks interesting, what did you mean by sending me {str(caption)}?",
        ]
    )
