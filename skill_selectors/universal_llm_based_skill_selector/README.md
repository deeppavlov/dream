# Universal LLM-based Skill Selector

## Description

Debugging Skill Selector is a component selecting a list of skills to generate hypotheses.
The LLM-based Skill Selector utilizes LLM service to select the skills in a generative manner.
The considered LLM-service, generative parameters and prompt  are provided IN attributes of 
the last human utterance. The list of all available skills is picked up from human utterance attributes.


**Important** Provide `"return_all_hypotheses": True` (to return joined list of all returned hypotheses) 
and `"selected_skills": "all"` (to turn on dff_universal_prompted_skill because all other prompted skills
are not deployed during debugging process).

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
            "skill_name": ["Mathematician Skill", "blondy_skill"],
            "prompt": ["Answer as a mathematician.", "Answer like you are a stupid Blondy Girl."], 
            "lm_service_url": [LM_SERVICES_MAPPING[lm_service], LM_SERVICES_MAPPING[lm_service]],
            "lm_service_config": [
                {
                    "max_new_tokens": 64,
                    "temperature": 0.9,
                    "top_p": 1.0,
                    "frequency_penalty": 0,
                    "presence_penalty": 0
                }, 
                None
            ],
            "lm_service_kwargs": [
                {"openai_api_key": "FILL IN"},
                {"openai_api_key": "FILL IN"}
            ],
            # ---------------------------- response selector MUST RETURN ALL HYPOTHESES JOINED
            "return_all_hypotheses": True,
            # ---------------------------- skill selector 
            "selected_skills": "all", # must use it to turn on universal skill (others are not deployed!)
            "skill_selector_prompt": """
Select up to 2 the most relevant to the dialog context skills based on the given short descriptions of abilities of different skills of the assistant.

Skills:
"Mathematician Skill": "A skill pretending to be a mathematician."
"blondy_skill": "A Skill pretending to be a blondy girl."

Return only names of the selected skills divided by comma. Do not respond to the dialog context.""", 
            "skill_selector_lm_service_url": LM_SERVICES_MAPPING[lm_service],
            "skill_selector_lm_service_config": 
                {
                    "max_new_tokens": 64,
                    "temperature": 0.4,
                    "top_p": 1.0,
                    "frequency_penalty": 0,
                    "presence_penalty": 0
                },
            "skill_selector_lm_service_kwargs": {"openai_api_key": "FILL IN"},
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

The algorithm utilizes `N_UTTERANCES_CONTEXT` last utterances as a context for LLM.
Number of returned skills can ve varied by the prompt itself.

## Dependencies

- generative service `DEFAULT_LM_SERVICE_URL` or the given in attributes in the last human utterance