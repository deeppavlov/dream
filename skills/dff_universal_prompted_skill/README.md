# DFF Universal Prompted Skill

## Description

This skill is aimed for debugging purposes, it utilizes the given in the request to the dialog system (!)
LLM service to generate a response to the given dialog context and prompt.

Use it in the following way:

1. raise a dialog system with the skill
2. send a request to it from python in the folllowing way:
```python
import random
import requests

prompt = """Your prompt here"""
lm_service = "http://openai-api-chatgpt:8145/respond"  # or any other from the added to your distribution
UNIVERSAL_ASSISTANT = "http://0.0.0.0:4242"  # if the agent raised locally on the same server

result = requests.post(
     UNIVERSAL_ASSISTANT, 
     json={
         "user_id": f"test-user-000", 
         "payload": "Who are you? who built you? what can you do?",
         "skills": [
            {
                "name": "dff_34857435_prompted_skill",
                "display_name": "Mathematician Skill",
                "description": "Mathematician Skill imitating an intelligent person.", 
                "prompt": "Answer like you are mathematician.",
                "lm_service": {
                    "url": lm_service,
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
         ],
         "api_keys": {
             "openai_api_key": "FILL-IN"
         },
         "debug_output": True,
     }).json()
```

### Parameters

```
DEFAULT_LM_SERVICE_TIMEOUT: default timeout for request to LLM
N_UTTERANCES_CONTEXT: number of last utterances to consider as a dialog context
DEFAULT_LM_SERVICE_URL: default LLM to utilize if not provided in the request
DEFAULT_LM_SERVICE_CONFIG: onfiguration file with generative parameters to utilize if not provided in the request
```

## Dependencies

- LLM `GENERATIVE_SERVICE_URL`
- API keys in environmental variables for key-required LLMs (OpenAI API, Anthropic API)