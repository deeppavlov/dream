
# Anthropic API Service


Service for Anthropic API LLMs connection.

### Parameters

Parameter `PRETRAINED_MODEL_NAME_OR_PATH` defines which model to use. Supported models are:
- "claude-1"
- "claude-instant-1"
- Any other, if one creates a new container with the considered model name

## Dependencies

- Depends only on the stability of Anthropic API.
- Incoming requests to the service must contain valid Anthropic API key.
