
# anthropic-claude APIs 

## Description
component_type: Generative
model_type: NN-based
is_customizable: false

The Anthropic API controls which version of Claude answers your request. 
Right now the two model families are available: Claude and Claude Instant.

[Anthropic Claude-v1](https://docs.anthropic.com/claude/reference/complete_post) is the largest Anthropic model, ideal for a wide range of more complex tasks. 

[Anthropic Claude Instant v1](https://docs.anthropic.com/claude/reference/complete_post) is a smaller model with far lower latency, sampling at roughly 40 words/sec! Its output quality is somewhat lower than the latest claude-1 model, particularly for complex tasks. However, it is much less expensive and blazing fast. 

For more details, refer to [Anthropic website](https://console.anthropic.com/docs/api/reference).

NB: Access to both services is granted via paid subscription. You must provide your Anthropic API key to use the model. Your Anthropic API account will be charged according to your usage.

## I/O
...

## Dependencies

Configuration settings specified in the .yaml files for [anthropic-api-claude-v1](service_configs/anthropic-api-claude-v1) and [anthropic-api-claude-instant-v1](service_configs/anthropic-api-claude-instant-v1)

Required Python packages specified in [requirements.txt](requirements.txt).