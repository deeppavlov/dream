# Ranking-based Response Selector

## Description

Response Selector is a component selecting final response among the given hypotheses by different skills.
The Ranking-based Response Selector utilizes floating point annotations by ranking candidate annotator (e.g., Sentence Ranker)
to rank hypotheses and selects the best ranked one.

### Parameters

Utilizes annotations by `SENTENCE_RANKER_ANNOTATION_NAME` candidate annotator. If these annotations are absent, utilizes provided `SENTENCE_RANKER_SERVICE_URL` to annotate hypotheses 
according to `N_UTTERANCES_CONTEXT` last utterances.

Parameter `FILTER_TOXIC_OR_BADLISTED` defines whether to filer out toxic hypotheses or not.

Parameter `ENABLE_FACT_CHECKING` defines whether to filter out factually incorrect hypotheses. To define if a hypothesis is factually correct, Response Selector either uses the existing candidate annotation specified in `FACTUAL_CONFORMITY_ANNOTATION_NAME` or posts requests to the service or annotator specified in `FACTUAL_CONFORMITY_SERVICE_URL` with `FACTUAL_CONFORMITY_SERVICE_TIMEOUT` timeout.


## Dependencies

- either candidate annotations by `SENTENCE_RANKER_ANNOTATION_NAME` or service `SENTENCE_RANKER_SERVICE_URL`
- __only if `ENABLE_FACT_CHECKING=1`:__ either candidate annotations by `FACTUAL_CONFORMITY_ANNOTATION_NAME` or service `FACTUAL_CONFORMITY_SERVICE_URL`