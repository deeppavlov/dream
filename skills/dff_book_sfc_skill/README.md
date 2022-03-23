# Book skill (DFF)
This service handles typical book questions.
It can recommend books according to user's preferences.
Unlike the original Book Skill, this Skill has been augmented with the MIDAS classifier and predictor.

# If you want to use MIDAS in DFF DSL

To use MIDAS as conditions for transition to the next node, you can write in TRANSITIONS
`"transition_node_name": dm_cnd.is_midas("pos_answer")`.

To use MIDAS to specify a dialog act of a bot's utterance to be able to make predictions for this utterance, you can write in MISC
`"dialog_act": ["open_question_factual"]`

# All dialog acts available for use
Here is a list of all dialog acts available for use in this version: <br>

| MIDAS | Explanation | Example |
| --- | --- | --- |
| appreciation | appreciation towards the previous utterance | that’s cool; that’s really awesome |
| command | commands/requests (can be in a question format) for some actions that may be different from the ongoing conversation | can i ask you a question; let’s talk about the immigration policy; repeat |
| comment | comments on the response from another conversation party | (A: my friend thinks we live in the matrix) B1: she is probably right; B2: you are joking, right; B3: i agree; (A: ... we can learn a lot from movies ...) B: there is a lot to learn; (A: He is the best dancer after michael jackson. What do you think) B: michael jackson |
| complaint | complaint about the response from another party | I can’t hear you; what are you talking about; you didn’t answer my question |
| dev_command | general device/system commands | show me the best games of this month |
| neg_answer | negative response to a previous question | no; not really; nothing right now |
| open_question_factual | factual questions | How old is Tom Cruise; How’s the weather today |
| open_question_opinion | opinionated questions | What’s your favorite book; what do you think of disney movies |
| opinion | personal view with polarized sentiment | dogs are adorable; (A: How do you like Tom) B: i think he is great |
| other_answers | answers that are neither positive or negative | I don’t know; i don’t have a favorite; (A: do you like listening to music) B: occasionally |
| pos_answer | positive answers | yes; sure; i think so; why not |
| statement | factual information | I have a dog named Max; I am 10 years old; (A: what movie have you seen recently) B: the avengers |
| yes_no_question | opinionated questions | What’s your favorite book; what do you think of disney movies |


# Metrics

OS: Windows 10
CPU: AMD Ryzen 5 3500U @ 2.10GHz

| Metric       | Average value |
| ------------ | ------------- |
| RAM          | ~ 385 MB      |
| Startup time | ~  3.985s     |
| Execute time | ~  2.687s     |
