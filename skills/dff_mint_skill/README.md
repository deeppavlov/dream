# dff_mint_skill

This is the skill for dream_mint distribution that allows Dream to respond to caught specific user intents.

The notable part of this skill may be found at `scenario/response_funcs.py`:
If the skill was chosen by dream, the skill checks whether the command Dream want's the connector to execute is valid, and if so, it sets the `command_to_perform` attribute to be equal to the command's name.