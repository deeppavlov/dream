from dff.script import Context
from .processing import DREAM_SLOTS_KEY
from .message import DreamMessage


def fill_by_slots(response: DreamMessage):
    def fill_responses_by_slots_inner(
        ctx: Context,
        _,
        *args,
        **kwargs,
    ) -> Context:
        if not response.text:
            return response
        for slot_name, slot_value in ctx.misc.get(DREAM_SLOTS_KEY, {}).items():
            response.text = response.text.replace("{" f"{slot_name}" "}", slot_value)
        return response

    return fill_responses_by_slots_inner
