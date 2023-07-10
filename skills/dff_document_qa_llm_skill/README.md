# LLM-based Q&A on Documents Skill

## Description

LLM-based Q&A on Documents Skill answers questions about long documents provided by the user. It passes on document chunks most relevant to the user's question alongside with an instruction and the dialog context as a prompt to ChatGPT.

## Parameters

```
GENERATIVE_SERVICE_URL: LLM to utilize
GENERATIVE_SERVICE_CONFIG: configuration file with generative parameters to utilize
GENERATIVE_TIMEOUT: timeout for request to LLM
N_UTTERANCES_CONTEXT: number of last utterances to consider as a dialog context
ENVVARS_TO_SEND: API keys splitted by comma to get as env variables
FILE_SERVER_TIMEOUT: timeout for request where files are stored
DOCUMENT_PROMPT_FILE: file to get the instruction from (to insert into prompt guiding the Question Answering model)
```

## Dependencies

- LLM service provided in `GENERATIVE_SERVICE_URL`
- annotator Document Retriever (both endpoints)
- API keys in environmental variables for key-required LLMs (OpenAI API, Anthropic API)


## How to get OpenAI API key

Go to OpenAI and find your Secret API key in your [user settings](https://platform.openai.com/account/api-keys).