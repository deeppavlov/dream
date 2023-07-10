# LLM-based Q&A on Documents Skill

## Description

Document-based LLM QA is a distribution of Dream designed to answer questions about the content of one or several documents supplied by the user. This distribution uses TF-IDF vectorization and cosine similarity to detect parts of documents most relevant to the user’s question. N most relevant parts, alongside with an instruction and the dialog context are then passed on to ChatGPT as a prompt.

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