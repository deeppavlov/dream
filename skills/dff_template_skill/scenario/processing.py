import logging

# from dff.core import Node, Context, Actor


logger = logging.getLogger(__name__)
# ....


# def fill_slots(node_label: str, node: Node, ctx: Context, actor: Actor, *args, **kwargs):
#     for slot_name, slot_value in ctx.misc.get("slots", {}).items():
#         node.response = node.response.replace("{" f"{slot_name}" "}", slot_value)
#     return node_label, node
