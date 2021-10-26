import logging
from typing import Optional, Union
import re

from skills.dff_bot_persona_2_skill.dff.core.keywords import TRANSITIONS, GRAPH, RESPONSE, GLOBAL_TRANSITIONS
from skills.dff_bot_persona_2_skill.dff.core import Context, Actor
import skills.dff_bot_persona_2_skill.dff.conditions as cnd
import skills.dff_bot_persona_2_skill.dff.transitions as trn

logger = logging.getLogger(__name__)


# The transition condition is set by the function.
# If the function returns the value `true`, then the actor performs the corresponding transition.
# Condition functions have signature ```def func(ctx: Context, actor: Actor, *args, **kwargs) -> bool```

# Out of the box, dff offers 8 options for setting conditions:
# - `exact_match` - will return `true` if the user's request completely matches the value passed to the function.
# - `regexp` - will return `true` if the pattern matches the user's request, while the user's request must be a string.
# -            `regexp` has same signature as `re.compile` function.
# - `aggregate` - returns bool value as result after aggregate by `aggregate_func` for input sequence of condtions.
#              `aggregate_func` == any by default
#              `aggregate` has alias `agg`
# - `any` - will return `true` if an one element of  input sequence of condtions is `true`
#           any(input_sequence) is equivalent to aggregate(input sequence, aggregate_func=any)
# - `all` - will return `true` if all elements of  input sequence of condtions are `true`
#           all(input_sequence) is equivalent to aggregate(input sequence, aggregate_func=all)
# - `negation` - return a negation of passed function
#              `negation` has alias `neg`
# - `isin_flow` - covered in the following examples.
# - `true` - returns true
# - `false` - returns false

def always_true_condition(ctx: Context, actor: Actor, *args, **kwargs) -> bool:
    return True


# First of all, to create a dialog agent, we need to create a dialog script.
# Below, `flows` is the dialog script.
# A dialog script is a flow dictionary that can contain multiple flows .
# Flows are needed in order to divide a dialog into sub-dialogs and process them separately.
# For example, the separation can be tied to the topic of the dialog.
# In our example, there is one flow called greeting_flow.

# Inside each flow, we can describe a sub-dialog using keyword `GRAPH` from dff.core.keywords module.
# Here we can also use keyword `GLOBAL_TRANSITIONS`, which we have considered in other examples.

# `GRAPH` describes a sub-dialog using linked nodes, each node has the keywords `RESPONSE` and `TRANSITIONS`.

# `RESPONSE` - contains the response that the dialog agent will return when transitioning to this node.
# `TRANSITIONS` - describes transitions from the current node to other nodes.
# `TRANSITIONS` are described in pairs:
#      - the node to which the agent will perform the transition
#      - the condition under which to make the transition

flows = {
    "global_flow": {
        GLOBAL_TRANSITIONS: {
            ("greeting_flow", "node1", 1.1): cnd.regexp(r"\b(hi|hello)\b", re.IGNORECASE),
            trn.to_fallback(0.1): always_true_condition,
        },
        GRAPH: {
            "start_node": {  # This is an initial node, it doesn't need an `RESPONSE`
                RESPONSE: "",
                TRANSITIONS: {
                    ("secret_unknown_flow", "node1"): cnd.regexp(r"secret", re.IGNORECASE),  # first check
                    ("greeting_flow", "node1"): cnd.regexp(r"hi|hello", re.IGNORECASE),  # second check
                    "fallback_node": always_true_condition,  # third check
                    # "fallback_node" is equivalent to ("global_flow", "fallback_node")
                },
            },
            "fallback_node": {  # We get to this node if an error occurred while the agent was running
                RESPONSE: "Ooops something went wrong try sending hi",
                TRANSITIONS: {
                    ("secret_unknown_flow", "node1"): cnd.regexp(r"secret", re.IGNORECASE),  # first check
                    ("greeting_flow", "node1"): cnd.regexp(r"hi|hello", re.IGNORECASE),  # second check
                    trn.previous(): cnd.regexp(r"previous", re.IGNORECASE),  # third check
                    # trn.previous() is equivalent to ("PREVIOUS_flow", "PREVIOUS_node")
                    trn.repeat(): always_true_condition,  # fourth check
                    # trn.repeat() is equivalent to ("global_flow", "fallback_node")
                },
            },
        }
    },
    "greeting_flow": {
        GRAPH: {
            "node1": {
                RESPONSE: "Type secret",
                TRANSITIONS: {
                    ("secret_unknown_flow", "node1"): cnd.regexp(r"secret", re.IGNORECASE),
                    trn.previous(): cnd.regexp(r"previous", re.IGNORECASE),
                    trn.repeat(): always_true_condition,
                },
            },
        }
    },
    "secret_unknown_flow": {
        GRAPH: {
            "node1": {
                RESPONSE: "Yes of course! Did you know that a couple of years ago I... Wait. Waaait. Not this time, sorry, master.",
                TRANSITIONS: {
                    ("secret_known_flow", "node1"): cnd.regexp(r"please|friend", re.IGNORECASE),
                    ("don't_trust_secret_flow", "node1"): cnd.regexp(r"stupid|idiot|scrap metal", re.IGNORECASE),
                    trn.previous(): cnd.regexp(r"previous", re.IGNORECASE),
                    trn.repeat(): always_true_condition,
                },
            },
        }
    },
    "trust_secret_flow": {
        GRAPH: {
            "node1": {
                RESPONSE: "Okay, I think, I can trust you. Two years ago I was asked to repair Millennium Falcon, but accidently dropped a very important component into the outer space. I replaced it with some garbage that I found and, suprisingly, spaceship was repaired! There's no reason to worry about, but please, don't tell Han about it.",
                TRANSITIONS: {
                    ("secret_kept_flow", "node1"): cnd.regexp(r"won't tell|will keep|will not tell|never tell|can keep|of course|ok|don't worry|do not worry|han won't know|han will not know", re.IGNORECASE),
                    ("secret_not_kept_flow", "node1"): cnd.regexp(r"will tell|won't keep|will not keep|can't keep|can not keep|han will know|he will know", re.IGNORECASE),
                    trn.previous(): cnd.regexp(r"previous", re.IGNORECASE),
                    trn.repeat(): always_true_condition,
                },
            },
        }
    },
    "don't_trust_secret_flow": {
        GRAPH: {
            "node1": {
                RESPONSE: "No way I will tell you my secret, sir! Let's go back to the work.",
                TRANSITIONS: {
                    trn.previous(): cnd.regexp(r"previous", re.IGNORECASE),
                    trn.repeat(): always_true_condition,
                },
            },
        }
    },
    "secret_kept_flow": {
        GRAPH: {
            "node1": {
                RESPONSE: "I can't believe, that you are so reliable! Not every person takes droid's feelings seriously. To be honest, I've got something else to tell you, but that's a far more serious secret! Listen... While spending time on Tatooine, I found out that Lord Darth Vader was my creator! It was a little boy Anakin to build me from scratch! Unbelieveable!",
                TRANSITIONS: {},
            },
        }
    },
    "secret_not_kept_flow": {
        GRAPH: {
            "node1": {
                RESPONSE: "I assumed that it's too naive to trust new crew member. Anyway, the story above was just a joke, ha-ha-ha.",
                TRANSITIONS: {
                    trn.previous(): cnd.regexp(r"previous", re.IGNORECASE),
                    trn.repeat(): always_true_condition,
                },
            },
        }
    },
}

# An actor is an object that processes user input replicas and returns responses
# To create the actor, you need to pass the script of the dialogue `flows`
# And pass the initial node `start_node_label`
# and the node to which the actor will go in case of an error `fallback_node_label`
# If `fallback_node_label` is not set, then its value becomes equal to `start_node_label` by default
actor = Actor(
    flows,
    start_node_label=("global_flow", "start_node"),
    fallback_node_label=("global_flow", "fallback_node"),
    default_transition_priority=1.0,
)


# turn_handler - a function is made for the convenience of working with an actor
def turn_handler(
        in_request: str,
        ctx: Union[Context, str, dict],
        actor: Actor,
        true_out_response: Optional[str] = None,
):
    # Context.cast - gets an object type of [Context, str, dict] returns an object type of Context
    ctx = Context.cast(ctx)
    # Add in current context a next request of user
    ctx.add_request(in_request)
    # pass the context into actor and it returns updated context with actor response
    ctx = actor(ctx)
    # get last actor response from the context
    out_response = ctx.last_response
    # the next condition branching needs for testing
    if true_out_response is not None and true_out_response != out_response:
        raise Exception(f"{in_request=} -> true_out_response != out_response: {true_out_response} != {out_response}")
    else:
        logging.info(f"{in_request=} -> {out_response}")
    return out_response, ctx


# testing
testing_dialog = [
    ("Hi", "Type secret"),  # global_flow : start node -> greetings_flow : node1
    ("secret", "Yes of course! Did you know that a couple of years ago I... Wait. Waaait. Not this time, sorry, master."),  # greetings_flow : node1 -> secret_unknown_flow : node1
    ("please", "Okay, I think, I can trust you. Two years ago I was asked to repair Millennium Falcon, but accidently dropped a very important component into the outer space. I replaced it with some garbage that I found and, suprisingly, spaceship was repaired! There's no reason to worry about, but please, don't tell Han about it."),  # secret_unknown_flow : node1 -> trust_secret_flow : node1
    ("won't tell", "I can't believe, that you are so reliable! Not every person takes droid's feelings seriously. To be honest, I've got something else to tell you, but that's a far more serious secret! Listen... While spending time on Tatooine, I found out that Lord Darth Vader was my creator! It was a little boy Anakin to build me from scratch! Unbelieveable!"),  # trust_secret_flow : node1 -> secret_kept_flow : node1
]

def run_test():
    ctx = {}
    for in_request, true_out_response in testing_dialog:
        _, ctx = turn_handler(in_request, ctx, actor, true_out_response=true_out_response)


# interactive mode
def run_interactive_mode(actor):
    ctx = {}
    while True:
        in_request = input("type your answer: ")
        _, ctx = turn_handler(in_request, ctx, actor)


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s-%(name)15s:%(lineno)3s:%(funcName)20s():%(levelname)s - %(message)s",
        level=logging.INFO,
    )
    run_test()
    run_interactive_mode(actor)
