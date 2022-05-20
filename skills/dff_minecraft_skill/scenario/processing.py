import logging
import re
from xmlrpc.client import boolean
import common.dff.integration.context as int_ctx
import common.dff.integration.processing as int_prs
import common.minecraft.core.serializer as serializer
from df_engine.core import Context, Actor


logger = logging.getLogger(__name__)

GO_TO_COMPILED_PATTERN = re.compile(r"(?:(?:go to)|(?:move to)|(?:come to)) (\d+)\s*\,*\s*(\d+)\s*\,*\s*(\d+)", re.IGNORECASE)

def add_encoding_for_goto():
    def add_encoding_processing(ctx: Context, actor: Actor, *args, **kwargs) -> Context:
        processed_node = ctx.framework_states["actor"].get("processed_node", ctx.framework_states["actor"]["next_node"])
        utt = ctx.misc["agent"]["dialog"]['human_utterances'][-1]['text']
        results = re.findall(GO_TO_COMPILED_PATTERN, utt)
        actions_list = [{"action": "goto", "args": [results[0][0], results[0][1], results[0][2]], "kwargs": {"range_goal": 1}}]
        processed_node.response = f"{processed_node.response} #+# {serializer.encode_actions(actions_list)}"
        ctx.framework_states["actor"]["processed_node"] = processed_node
        return ctx

    return add_encoding_processing


def add_encoding_for_look_at_user():
    def add_encoding_processing(ctx: Context, actor: Actor, *args, **kwargs) -> Context:
        processed_node = ctx.framework_states["actor"].get("processed_node", ctx.framework_states["actor"]["next_node"])
        utt = ctx.misc["agent"]["dialog"]['human_utterances'][-1]['text']
        actions_list = [{"action": "look_at_user", "args": [], "kwargs": {}}]
        processed_node.response = f"{processed_node.response} #+# {serializer.encode_actions(actions_list)}"
        ctx.framework_states["actor"]["processed_node"] = processed_node
        return ctx

    return add_encoding_processing


def add_encoding_for_stop():
    def add_encoding_processing(ctx: Context, actor: Actor, *args, **kwargs) -> Context:
        processed_node = ctx.framework_states["actor"].get("processed_node", ctx.framework_states["actor"]["next_node"])
        utt = ctx.misc["agent"]["dialog"]['human_utterances'][-1]['text']
        actions_list = [{"action": "stop", "args": [], "kwargs": {}}]
        processed_node.response = f"{processed_node.response} #+# {serializer.encode_actions(actions_list)}"
        ctx.framework_states["actor"]["processed_node"] = processed_node
        return ctx

    return add_encoding_processing


def add_encoding_no_range(action_name: str, should_follow: bool = False):
    def add_encoding_processing(ctx: Context, actor: Actor, *args, **kwargs) -> Context:
        processed_node = ctx.framework_states["actor"].get("processed_node", ctx.framework_states["actor"]["next_node"])

        # For Response Selector; for good UX 2 loops are good though
        # actions_list = [{"action": "chat", "args": [], "kwargs": {"range_goal": 1, "nod_head" : True, "animation_loops" : 2}}]
        # actions_list = [{"action": "chat", "args": [], "kwargs": {"range_goal": 1, "shake_head" : True, "animation_loops" : 2}}]

        # loops - for debugging
        # actions_list = [{"action": "chat", "args": [], "kwargs": {"range_goal": 1, "shake_head" : True, "animation_loops" : 1}}]

        actions_list = [{"action": action_name, "args": [], "kwargs": {}}]
        processed_node.response = f"{processed_node.response} #+# {serializer.encode_actions(actions_list)}"
        ctx.framework_states["actor"]["processed_node"] = processed_node
        return ctx

    return add_encoding_processing


def add_encoding(action_name: str, should_follow: bool = False):
    def add_encoding_processing(ctx: Context, actor: Actor, *args, **kwargs) -> Context:
        processed_node = ctx.framework_states["actor"].get("processed_node", ctx.framework_states["actor"]["next_node"])

        # For Response Selector; for good UX 2 loops are good though
        # actions_list = [{"action": "chat", "args": [], "kwargs": {"range_goal": 1, "nod_head" : True, "animation_loops" : 2}}]
        # actions_list = [{"action": "chat", "args": [], "kwargs": {"range_goal": 1, "shake_head" : True, "animation_loops" : 2}}]

        # loops - for debugging
        # actions_list = [{"action": "chat", "args": [], "kwargs": {"range_goal": 1, "shake_head" : True, "animation_loops" : 1}}]

        actions_list = [{"action": action_name, "args": [], "kwargs": {"range_goal": 1, "follow" : should_follow}}]
        processed_node.response = f"{processed_node.response} #+# {serializer.encode_actions(actions_list)}"
        ctx.framework_states["actor"]["processed_node"] = processed_node
        return ctx

    return add_encoding_processing
