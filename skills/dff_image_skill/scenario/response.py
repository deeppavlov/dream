import logging
import random 
from df_engine.core import Context, Actor
from common.dff.integration import condition as int_cnd
import common.dff.integration.context as int_ctx
import scenario.processing as loc_prs

logger = logging.getLogger(__name__)

def animals_response(ctx: Context, actor: Actor, excluded_skills=None, *args, **kwargs) -> str:
    caption = int_ctx.get_last_human_utterance(ctx, actor).get("annotations", {}).get("image_captioning", {}).get("caption", {})
    animal = {loc_prs.extract_entity(str(caption), loc_prs.get_all_possible_entities("animal"))}
    int_ctx.set_confidence(ctx, actor, 1)
    return random.choice(['What a muzzle! Would you like to have an animal like that?', 
                          'I would like to have an animal like that. I wonder if it eats a lot.',
                          f'Is it your {animal}?'])

def food_response(ctx: Context, actor: Actor, excluded_skills=None, *args, **kwargs) -> str:
    caption = int_ctx.get_last_human_utterance(ctx, actor).get("annotations", {}).get("image_captioning", {}).get("caption", {})
    food = loc_prs.extract_entity(str(caption), loc_prs.get_all_possible_entities("food"))
    int_ctx.set_confidence(ctx, actor, 1)
    return random.choice([f'Did you cook this {food} by yourself? It looks delicious!',
                          f'Would you like to eat this {food}?'])

def people_response(ctx: Context, actor: Actor, excluded_skills=None, *args, **kwargs) -> str:
    caption = str(int_ctx.get_last_human_utterance(ctx, actor).get("annotations", {}).get("image_captioning", {}).get("caption", {}))
    verb = loc_prs.extract_verb_from_sentence(caption)
    int_ctx.set_confidence(ctx, actor, 1)
    return f'Do you enjoy {verb} with other people?'

def generic_response(ctx: Context, actor: Actor, excluded_skills=None, *args, **kwargs) -> str:
    caption = int_ctx.get_last_human_utterance(ctx, actor).get("annotations", {}).get("image_captioning", {}).get("caption", {})
    int_ctx.set_confidence(ctx, actor, 1)
    return random.choice([f'Cool! Why did you send me {caption}?', f'It looks interesting, what did you mean by sending me {caption}?'])