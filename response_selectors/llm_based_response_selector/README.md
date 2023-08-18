# LLM-based Response Selector

## Description

Response Selector is a component selecting final response among the given hypotheses by different skills.
The LLM-based Response Selector utilizes LLM with to select the best hypotheses in a generative manner.


### Parameters

The algorithm sends request to the LLM on `GENERATIVE_SERVICE_URL` with a generative parameters 
in `GENERATIVE_SERVICE_CONFIG` and timeout `GENERATIVE_TIMEOUT`. The algorithm utilizes `N_UTTERANCES_CONTEXT`
last utterances as a context for LLM, and `PROMPT_FILE` for hypotheses selection:
```python
import json
from os import getenv


PROMPT_FILE = getenv("PROMPT_FILE")
assert PROMPT_FILE
with open(PROMPT_FILE, "r") as f:
    PROMPT = json.load(f)["prompt"]
```

Parameter `FILTER_TOXIC_OR_BADLISTED` defines whether it filers out toxic hypotheses or not.

## Dependencies

- generative service `GENERATIVE_SERVICE_URL`