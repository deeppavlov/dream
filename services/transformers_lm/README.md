# Transformers LLM Service

## Description

Service for LLMs connection from HuggingFace transformers.

### Parameters

Parameter `PRETRAINED_MODEL_NAME_OR_PATH` defines which model to use. Supported models are:
- "EleutherAI/gpt-j-6B" (not available via proxy
- "OpenAssistant/pythia-12b-sft-v8-7k-steps" (available via Proxy)
- "togethercomputer/GPT-JT-6B-v1" (available via Proxy)
- "lmsys/vicuna-13b-v1.3" (not available via proxy)
- Any other, if one creates a new container with the considered model name and raise it locally.

## Dependencies

- When using via Proxy, depends on Proxy stability.
