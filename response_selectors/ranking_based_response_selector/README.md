# Ranking-based Response Selector

## Description

Response Selector is a component selecting final response among the given hypotheses by different skills.
The Ranking-based Response Selector utilizes floating point annotations by ranking candidate annotator (e.g., Sentence Ranker)
to rank hypotheses and selects the best ranked one.

### Parameters

Utilizes annotations by `SENTENCE_RANKER_ANNOTATION_NAME` candidate annotator.
In case of absence of these annotations, utilizes provided `SENTENCE_RANKER_SERVICE_URL` to annotate hypotheses
according to `N_UTTERANCES_CONTEXT` last utterances.
Parameter `FILTER_TOXIC_OR_BADLISTED` defines whether it filers out toxic hypotheses or not.

**Output:**
Ranking_based_response_selector service returns
+ the selected skill’s name,
+ the response text (which can be overwritten)
+ the confidence level
+ the selected skill name,
+ the response text (which can be overwritten)
+ the confidence level

A partial example of such a response selector's output:

```
{
              "skill_name": "movie_tfidf_retrieval",
              "annotations": {
                "toxic_classification": {
                  "identity_hate": 0.0001259446144104004,
                  "insult": 0.00027686357498168945,
                  "obscene": 5.97834587097168e-05,
                  "severe_toxic": 3.403425216674805e-05,
                  "sexual_explicit": 8.13603401184082e-05,
                  "threat": 0.00012931227684020996,
                  "toxic": 0.0005629658699035645
                },
                "stop_detect": {
                  "stop": 0.5833511352539062,
                  "continue": 0.46003755927085876
                },
                "convers_evaluator_annotator": {
                  "isResponseComprehensible": 0.281,
                  "isResponseErroneous": 0.531,
                  "isResponseInteresting": 0.228,
                  "isResponseOnTopic": 0.254,
                  "responseEngagesUser": 0.536
                },
                "badlisted_words": {
                  "inappropriate": false,
                  "profanity": false,
                  "restricted_topics": false
                }
              },
              "text": "i got you haha. what do you think about celebrities? judge judy makes 123, 000 per episode apparently!",
              "confidence": 0.38232852805460565
            },
``` 

## Dependencies

- either candidate annotations by `SENTENCE_RANKER_ANNOTATION_NAME` or service `SENTENCE_RANKER_SERVICE_URL`.

