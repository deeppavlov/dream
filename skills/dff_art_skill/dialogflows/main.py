from dff import Actor
from common.dff_markup_scenarios.art_scenario import flows


actor = Actor(flows, start_node_label=("beatles", "start"))
