# Meeting Analysis Skill

## Description

Meeting Analysis Skill analyses meeting transcripts. It uses generative models (`gpt-3.5-turbo` and `gpt-4`) to generate summary, list of key decisions and lists of current and completed tasks of each employee based on the entire meeting transcript.

## Parameters

```
SERVICE_PORT: 8186
SERVICE_NAME: dff_meeting_analysis_skill
GENERATIVE_SERVICE_URL: LLM to utilize
GENERATIVE_SERVICE_CONFIG: configuration file with generative parameters to utilize
GENERATIVE_TIMEOUT: timeout for request to LLM
SHORT_GENERATIVE_SERVICE_URL: LLM to utilize for check before using main GENERATIVE_SERVICE_URL
SHORT_GENERATIVE_SERVICE_CONFIG: configuration file with generative parameters to utilize for SHORT_GENERATIVE_SERVICE_URL
SHORT_GENERATIVE_TIMEOUT: timeout for request to LLM for SHORT_GENERATIVE_SERVICE_URL
N_UTTERANCES_CONTEXT: number of last utterances to consider as a dialog context
FILE_SERVER_TIMEOUT: timeout for request to the server where files are stored
```

## Dependencies

- LLM service provided in `GENERATIVE_SERVICE_URL`
- LLM service provided in `SHORT_GENERATIVE_SERVICE_URL`
- annotator Document Processor
- API keys in environmental variables for key-required LLMs (OpenAI API, Anthropic API)


## How to get OpenAI API key

Go to OpenAI and find your Secret API key in your [user settings](https://platform.openai.com/account/api-keys).