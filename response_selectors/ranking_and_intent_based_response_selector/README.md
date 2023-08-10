# Ranking- and Intent-based Response Selector

## Description

Response Selector is a component that selects the final response among hypotheses provided by different skills.
The Ranking- and Intent-based Response Selector utilizes floating point annotations by ranking hypotheses 
with a candidate annotator (e.g., Sentence Ranker), scaling the resulting scores with heuristics based 
on entities and intents, and finally selecting the best ranked one.

### Parameters

Utilizes annotations by `SENTENCE_RANKER_ANNOTATION_NAME` candidate annotator. 
In case of absence of these annotations, utilizes provided `SENTENCE_RANKER_SERVICE_URL` to annotate hypotheses 
according to `N_UTTERANCES_CONTEXT` last utterances.
Parameter `FILTER_TOXIC_OR_BADLISTED` defines whether it filers out toxic hypotheses or not.

## Dependencies

- either candidate annotations by `SENTENCE_RANKER_ANNOTATION_NAME` or service `SENTENCE_RANKER_SERVICE_URL`,
- intents annotations,
- entities annotations.
