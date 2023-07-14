# dff_mint_skill

This skill was mostly based on `dff_intent_responder_skill` from a `command_selector_distributions` branch (if it there is no longer such a branch, it was probably merged and said skill may be found in `dev` branch)

The notable part of this skill may be found at `scenario/response_funcs.py`:
even if the skill's hypothesis was chosen by dream, the skill checks yet again whether the command dream want's connector to execute is valid, and if so, it sets the `command_to_perform` to be equal to the command's name.