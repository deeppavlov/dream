# Universal LLM-based Response Selector

## Description

Debugging Response Selector is a component selecting final response among the given hypotheses by different skills.
The LLM-based Response Selector utilizes LLM with to select the best hypotheses in a generative manner.
The considered LLM-service, generative parameters, prompts and skill names are provided IN attributes of 
the last human utterance.

How to use:

```python
import requests
import random
from time import sleep


LM_SERVICES_MAPPING = {
    "ChatGPT": "http://openai-api-chatgpt:8145/respond",
}
for lm_service in ["ChatGPT"]:
    print(f"Checking `Universal Assistant` with `{lm_service}`")

    result = requests.post(
        "http://0.0.0.0:4242", 
        json={
            "user_id": f"test-user-{random.randint(100, 1000)}", 
            "payload": "How much is two plus two?",
            # ---------------------------- batch of universal skills to generate hypotheses
            "skills": [
                {
                    "name": "dff_34857435_prompted_skill",
                    "display_name": "Mathematician Skill",
                    "description": "Mathematician Skill imitating an intelligent person.", 
                    "prompt": "Answer like you are mathematician.",
                    "lm_service": {
                        "url": LM_SERVICES_MAPPING[lm_service],
                        "config": {
                            "max_new_tokens": 64,
                            "temperature": 0.9,
                            "top_p": 1.0,
                            "frequency_penalty": 0,
                            "presence_penalty": 0
                        }, 
                        "kwargs": None,
                    }
                },
                {
                    "name": "dff_bniu23rh_prompted_skill",
                    "display_name": "Blondy skill",
                    "description": "Skill for stupid funny responses imitating a blondy girl.",
                    "prompt": "Answer like you are a stupid Blondy Girl.",
                    "lm_service": {
                        "url": LM_SERVICES_MAPPING[lm_service],
                        "config": None, 
                        "kwargs": None,
                    }
                },
            ],
            # ---------------------------- response selector parameters
            "response_selector": {
                "prompt": "Select the most funny answer.\nLIST_OF_HYPOTHESES\n", 
                "lm_service": {
                    "url": LM_SERVICES_MAPPING[lm_service],
                    "config": 
                        {
                            "max_new_tokens": 64,
                            "temperature": 0.9,
                            "top_p": 1.0,
                            "frequency_penalty": 0,
                            "presence_penalty": 0
                        },
                    "kwargs": None,
                }
            },
            # ---------------------------- skill selector parameters
            "selected_skills": "all",
            "api_keys": {
                "openai_api_key": "FILL-IN"
            }
        }).json()
    print(f"Response:\n{result['response']}")
    if result["active_skill"] not in ["Dummy Skill", "dummy_skill"]:
        print("Success!")
    elif lm_service in ["ChatGPT", "GPT-3.5"]:
        print(f"\nATTENTION! OpenAI services do not work!\n")
    else:
        print(f"\nERROR: `Universal Assistant` returned `{result}`\n")
    sleep(5)
```

### Parameters

The algorithm utilizes `N_UTTERANCES_CONTEXT` last utterances as a context for LLM,
Parameter `FILTER_TOXIC_OR_BADLISTED` defines whether it filers out toxic hypotheses or not.

## Dependencies

- generative service `DEFAULT_LM_SERVICE_URL` or the given in attributes in the last human utterance