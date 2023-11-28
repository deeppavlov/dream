# DeepPavlov Dream MultiSkill-AI distribution

Distribution is a set of configuration files that define which components are used in this particular assistant.
This defines an assistant itself.

*(different Dream distributions may use different Annotators and Response Selectors, feature various Skills, and even speak different languages)*
- see how DeepPavlov Dream distribution works [here](https://docs.dream.deeppavlov.ai/dream_scheme.png)
- for full list of available distributions, click [here](https://docs.dream.deeppavlov.ai/ref_materials/distributions)

## Description
This DeepPavlov Dream distribution contains both DFF-template-based and Generative skills

## Services used in this DeepPavlov Dream Distribution
- sentseg
- llm-based-response-selector
- combined-classification
- sentence-ranker
- prompt-selector
- openai-api-chatgpt
- dff-dream-persona-chatgpt-prompted-skill
- dff-casual-email-prompted-skill
- dff-meeting-notes-prompted-skill
- dff-official-email-prompted-skill
- dff-plan-for-article-prompted-skill