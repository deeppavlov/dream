import logging
import random
from df_engine.core import Context, Actor
import common.dff.integration.context as int_ctx
import scenario.processing as loc_prs

logger = logging.getLogger(__name__)


def animals_response(ctx: Context, actor: Actor, excluded_skills=None, *args, **kwargs) -> str:
    int_ctx.set_confidence(ctx, actor, 1)
    captions = int_ctx.get_last_human_utterance(ctx, actor).get("annotations", {}).get("image_captioning", {})
    for caption in captions:
        animal = loc_prs.extract_entity(caption["caption"], loc_prs.get_all_possible_entities("animal"))
        responses = [f"Is it your {animal}?", "What a muzzle! Would you like to have an animal like that?", "I would like to have an animal like that. I wonder if it eats a lot."]
        return random.choice(responses)


def food_response(ctx: Context, actor: Actor, excluded_skills=None, *args, **kwargs) -> str:
    int_ctx.set_confidence(ctx, actor, 1)
    captions = int_ctx.get_last_human_utterance(ctx, actor).get("annotations", {}).get("image_captioning", {})
    for caption in captions:
        food = loc_prs.extract_entity(caption["caption"], loc_prs.get_all_possible_entities("food"))
        responses = [f"Did you cook this {food} by yourself? It looks delicious!", f"Would you like to eat this {food}?"]
        return random.choice(responses)


def people_response(ctx: Context, actor: Actor, excluded_skills=None, *args, **kwargs) -> str:
    int_ctx.set_confidence(ctx, actor, 1)
    captions = int_ctx.get_last_human_utterance(ctx, actor).get("annotations", {}).get("image_captioning", {})
    for caption in captions:
        verb = loc_prs.extract_verb_from_sentence(caption["caption"])
        return f"Do you enjoy {verb} with other people?"


def generic_response(ctx: Context, actor: Actor, excluded_skills=None, *args, **kwargs) -> str:
    int_ctx.set_confidence(ctx, actor, 1)
    captions = int_ctx.get_last_human_utterance(ctx, actor).get("annotations", {}).get("image_captioning", {})
    for caption in captions:
        return random.choice([f"Cool! Why did you send me {caption['caption']}?", f"It looks interesting, what did you mean by sending me {caption['caption']}?"])
