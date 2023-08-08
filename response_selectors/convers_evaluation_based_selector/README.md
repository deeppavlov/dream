# Tag- and Evaluation-based Response Selector

## Description

Response Selector is a component selecting final response among the given hypotheses by different skills.
The Tag- and Evaluation--based Response Selector utilizes a complicated approach which aims to
prioritize scripted skills while having an opportunity to provide a system-initiative via so called linking questions
that bring conversation to the scripts. A final hypotheses could be a combination of a hypotheses and linking question.
The approach is most suitable for distributions where the most of the responses are implied to be by scripts.

### Parameters

The algorithm contains a large number of parameters which control the filtration and prioritization rules. 
The algorithm filers out toxic hypotheses.

```
TAG_BASED_SELECTION: whether to use tag-based prioritization or simply utilize an empirical formula
CALL_BY_NAME_PROBABILITY: probability to add user's name if known
PROMPT_PROBA: probability to add linking question to a selected hypothesis
ACKNOWLEDGEMENT_PROBA: probability to add acknowledgement to a selected hypothesis
PRIORITIZE_WITH_REQUIRED_ACT: whether to prioritize hypotheses with a required dialog act (e.g., statement in response to user's question)
PRIORITIZE_NO_DIALOG_BREAKDOWN: whether to prioritize hypotheses classified as no-dialog-breakdown
PRIORITIZE_WITH_SAME_TOPIC_ENTITY: whether to prioritize hypotheses containing entities from the user's last utterance
IGNORE_DISLIKED_SKILLS: whether to ignore hypotheses by disliked skills (if user answers negatively to linking question to a skill, we add this skill to disliked ones)
GREETING_FIRST: whether to add greeting to the first bot's utterance
RESTRICTION_FOR_SENSITIVE_CASE: whether to avoid generative skills when sensitive case 
PRIORITIZE_PROMTS_WHEN_NO_SCRIPTS: whether to prioritize hypotheses tagged by `prompt` tag when no responses by scripted skills
MAX_TURNS_WITHOUT_SCRIPTS: maximum number of turns in a dialog without responses by scripted skills
ADD_ACKNOWLEDGMENTS_IF_POSSIBLE: whether to add acknowledgement to a selected hypothesis
PRIORITIZE_SCRIPTED_SKILLS: whether to prioritize scripted skills
CONFIDENCE_STRENGTH: confidence coefficient in a formula to compute a final score
CONV_EVAL_STRENGTH: annotator evaluation coefficient in a formula to compute a final score
PRIORITIZE_HUMAN_INITIATIVE: whether to prioritize human initiative (downscore scores of questions when user asked question)
QUESTION_TO_QUESTION_DOWNSCORE_COEF: coefficient to multiply scores of qustions when user asked question
LANGUAGE: language to consider
FALLBACK_FILE: a file name with fallbacks from `dream/common/fallbacks/`
```

## Dependencies


