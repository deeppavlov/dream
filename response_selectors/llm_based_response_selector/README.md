# LLM-based Response Selector

## Description

Response Selector is a component selecting final response among the given hypotheses by different skills.
The LLM-based Response Selector utilizes LLM with to select the best hypotheses in a generative manner.


### Parameters

The algorithm sends request to the LLM on `GENERATIVE_SERVICE_URL` with a generative parameters 
in `GENERATIVE_SERVICE_CONFIG` and timeout `GENERATIVE_TIMEOUT`. The algorithm utilizes `N_UTTERANCES_CONTEXT`
last utterances as a context for LLM, and `CRITERION` (by default, `the most appropriate, relevant and non-toxic`) 
to compose a prompt for hypotheses selection:
```python
from os import getenv


CRITERION = getenv("CRITERION", "the most appropriate, relevant and non-toxic")
PROMPT = (
    f"""Select {CRITERION} response among the hypotheses to the given dialog context. """
    """Return only the selected response without extra explanations."""
)
```

Parameter `FILTER_TOXIC_OR_BADLISTED` defines whether it filers out toxic hypotheses or not.

## Dependencies

- generative service `GENERATIVE_SERVICE_URL`