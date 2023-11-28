# DeepPavlov Dream Emotion distribution

Distribution is a set of configuration files that define which components are used in this particular assistant.
This defines an assistant itself.

*(different Dream distributions may use different Annotators and Response Selectors, feature various Skills, and even speak different languages)*
- see how DeepPavlov Dream distribution works [here](https://docs.dream.deeppavlov.ai/dream_scheme.png)
- for full list of available distributions, click [here](https://docs.dream.deeppavlov.ai/ref_materials/distributions)

## Description
This particular DeepPavlov Dream distribution focuses on a task of emotion classification during the dialogue, and contains a mix of Generative and DFF-template-based Skills. 


## Services used in this DeepPavlov Dream Distribution
- sentseg 
- combined-classification
- sentence-ranker
- prompt-selector
- openai-api-chatgpt
- dff-dream-persona-chatgpt-prompted-skill
- dff-dream-faq-prompted-skill
- openai-api-chatgpt-16k
- bot-emotion-classifier
- emotional-bot-response
- emotion-ranking-based-response-selector