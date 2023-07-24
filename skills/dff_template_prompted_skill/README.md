# DFF Template Prompted Skill

## Description

This skill utilizes the given LLM service to generate a response to the given dialog context and prompt.

### Parameters

```
PROMPT_FILE: prompt file path from dream root dir (e.g., `common/prompts/deeppavlov.json`)
GENERATIVE_SERVICE_URL: LLM to utilize
GENERATIVE_SERVICE_CONFIG: configuration file with generative parameters to utilize
GENERATIVE_TIMEOUT: timeout for request to LLM
N_UTTERANCES_CONTEXT: number of last utterances to consider as a dialog context
ENVVARS_TO_SEND: API keys splitted by comma to get as env variables (e.g., OPENAI_API_KEY, ANTHROPIC_API_KEY)
ALLOW_PROMPT_RESET: whether to allow prompt resetting with commands `/prompt bla` and `/resetprompt`. Actually, utilized only in DeepPavlov Assistant to provide an opportunity to change prompt for a particular user without re-building skill.
```

## Dependencies

- LLM `GENERATIVE_SERVICE_URL`
- API keys in environmental variables for key-required LLMs (OpenAI API, Anthropic API)