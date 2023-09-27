# Universal LLM-based Skill Selector

## Description

Debugging Skill Selector is a component selecting a list of skills to generate hypotheses.
The LLM-based Skill Selector utilizes LLM service to select the skills in a generative manner.
The considered LLM-service, generative parameters and prompt  are provided IN attributes of 
the last human utterance. The list of all available skills is picked up from human utterance attributes.

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
            # ---------------------------- get_debug_output to receive all hypotheses
            "debug_output": True,
            # ---------------------------- skill selector 
            "skill_selector": {
                "prompt": """
Select up to 2 the most relevant to the dialog context skills based on the given short descriptions of abilities of different skills of the assistant.

LIST_OF_AVAILABLE_AGENTS_WITH_DESCRIPTIONS

Return only names of the selected skills divided by comma. Do not respond to the dialog context.""",
                "lm_service": {
                    "url": LM_SERVICES_MAPPING[lm_service],
                    "config": 
                        {
                            "max_new_tokens": 64,
                            "temperature": 0.4,
                            "top_p": 1.0,
                            "frequency_penalty": 0,
                            "presence_penalty": 0
                        },
                    "kwargs": None,
                }
            },
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

    # all hypotheses could be accessed via the command:
    print([(hyp["skill_name"], hyp["text"]) for hyp in result["debug_output"]["hypotheses"]])
    # [('dummy_skill', "Sorry, probably, I didn't get what you meant. What do you want to talk about?"),
    #  ('dff_34857435_prompted_skill', 'Two plus two equals four.')]
```

### Parameters

The algorithm utilizes `N_UTTERANCES_CONTEXT` last utterances as a context for LLM.
Number of returned skills can ve varied by the prompt itself.

## Dependencies

- generative service `DEFAULT_LM_SERVICE_URL` or the given in attributes in the last human utterance