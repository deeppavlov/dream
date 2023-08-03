# dff_mint_skill

This is the skill for dream_mint distribution that allows Dream to respond to caught user mint Intents.

The notable part of this skill may be found at `scenario/response_funcs.py`:
even if the skill's hypothesis was chosen by dream, the skill checks yet again whether the command Dream want's connector to execute is valid, and if so, it sets the `command_to_perform` to be equal to the command's name.