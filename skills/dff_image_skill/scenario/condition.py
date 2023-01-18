import logging

from df_engine.core import Context, Actor
import common.dff.integration.context as int_ctx
import scenario.processing as loc_prs
import nltk

lmtzr = nltk.WordNetLemmatizer()

logger = logging.getLogger(__name__)
logger.setLevel(logging.NOTSET)


def detect_animals_on_caption_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    caption = (
        int_ctx.get_last_human_utterance(ctx, actor)
        .get("annotations", {})
        .get("image_captioning", {})
        .get("caption", {})
    )
    animal_on_caption = loc_prs.extract_entity(str(caption), loc_prs.get_all_possible_entities("animal"))
    if animal_on_caption != "":
        return True
    return False


def detect_food_on_caption_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    caption = (
        int_ctx.get_last_human_utterance(ctx, actor)
        .get("annotations", {})
        .get("image_captioning", {})
        .get("caption", {})
    )
    food_on_caption = loc_prs.extract_entity(str(caption), loc_prs.get_all_possible_entities("food"))
    if food_on_caption != "":
        return True
    return False


def detect_people_on_caption_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    caption = (
        int_ctx.get_last_human_utterance(ctx, actor)
        .get("annotations", {})
        .get("image_captioning", {})
        .get("caption", {})
    )
    person_on_caption = loc_prs.extract_entity(str(caption), loc_prs.get_all_possible_entities("person"))
    if person_on_caption != "":
        return True
    return False


def detect_other_on_caption_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    if any(
        [
            detect_animals_on_caption_condition(ctx, actor),
            detect_people_on_caption_condition(ctx, actor),
            detect_food_on_caption_condition(ctx, actor),
        ]
    ):
        return False
    return True
