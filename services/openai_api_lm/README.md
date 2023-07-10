# OpenAI API Service

## Description

Service for OpenAI API LLMs connection.

### Parameters

Parameter `PRETRAINED_MODEL_NAME_OR_PATH` defines which model to use. Supported models are:
- "text-davinci-003"
- "gpt-3.5-turbo"
- "gpt-3.5-turbo-16k"
- "gpt-4"
- "gpt-4-32k"
- Any other, if one creates a new container with the considered model name

## Dependencies

- Depends only on the stability of OpenAI API.
- Incoming requests to the service must contain valid OpenAI API key.
