import logging
import common.dff.integration.processing as int_prs
import common.dff.integration.context as int_ctx
from df_engine.core import Actor, Context
import requests
from os import getenv
# ....

logger = logging.getLogger(__name__)
# ....

SPACY_NOUN_PHRASES = getenv("SPACY_NOUN_PHRASES")


def save_previous_utterance(slot_name):

    def previous_human_utterance(
        ctx: Context,
        actor: Actor,
        *args,
        **kwargs,
    ) -> Context:
        human_text = int_ctx.get_nounphrases_from_human_utterance(ctx, actor)
        if human_text:
            ctx = int_prs.save_slots_to_ctx({slot_name: ' '.join(human_text)})(ctx, actor)
        return ctx

    return previous_human_utterance


def save_noun_phrase(slot_name): # NOT USED

    def get_noun_phrase(
        ctx: Context,
        actor: Actor,
        *args,
        **kwargs,
    ) -> Context:
        human_uttrs = int_ctx.get_human_utterances(ctx, actor)
        if len(human_uttrs) > 0:
            text_uttr =  human_uttrs[-1]["text"]
        else:
            text_uttr = ''
        input_data = {"sentences": [text_uttr]}
        result = requests.post(SPACY_NOUN_PHRASES, json=input_data)
        ctx = int_prs.save_slots_to_ctx({slot_name: str(input_data)})(ctx, actor)
        return ctx

    return get_noun_phrase

def save_user_name(slot_name):

    def get_name(
        ctx: Context,
        actor: Actor,
        *args,
        **kwargs,
    ) -> Context:
        human_text = str(int_ctx.get_nounphrases_from_human_utterance(ctx, actor))
        ctx = int_prs.save_slots_to_ctx({slot_name: human_text})(ctx, actor)
        return ctx

    return get_name

