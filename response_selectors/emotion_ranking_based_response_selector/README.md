# Emotion Ranking-based Response Selector

## Description

Response Selector is a component selecting final response among the given hypotheses by different skills.
The Emotion Ranking-based Response Selector utilizes floating point annotations by ranking candidate annotator (e.g., Sentence Ranker)
to rank hypotheses and selects emotional form of the best ranked one.

### Parameters

Utilizes annotations by `SENTENCE_RANKER_ANNOTATION_NAME` candidate annotator. 
In case of absence of these annotations, utilizes provided `SENTENCE_RANKER_SERVICE_URL` to annotate hypotheses 
according to `N_UTTERANCES_CONTEXT` last utterances.
Parameter `FILTER_TOXIC_OR_BADLISTED` defines whether it filers out toxic hypotheses or not.

## Dependencies

- either candidate annotations by `SENTENCE_RANKER_ANNOTATION_NAME` or service `SENTENCE_RANKER_SERVICE_URL`.