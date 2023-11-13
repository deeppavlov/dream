# Fact Checking

## Description

Fact Checking conducts basic fact-checking of response candidates. As of now, it considers all hypotheses derived from external sources correct. Internally generated hypotheses are fact-checked by ensuring that they do not contradict any of the external hypotheses. For example, if `dff_google_api_skill` that relies on Google as a source of external knowledge responds _"Person X is 25 years old"_ and some solely LLM-based skill provides a hallucinated responds _"Person X is 23 years old"_, the second hypotheses is considered incorrect as it contradicts the first, external one.

NB: Scripted responses from `dummy_skill` and `dff_intent_responder_skill` are not fact-checked for the sake of efficiency and are always deemed correct.

## Parameters

```
ENVVARS_TO_SEND: API keys splitted by comma to get as env variables
GENERATIVE_SERVICE_URL: LLM to utilize for fact-checking
GENERATIVE_TIMEOUT: timeout for the request to LLM
GENERATIVE_SERVICE_CONFIG:  configuration file with generative parameters to utilize
```
