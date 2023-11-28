# DeepPavlov Dream KG distribution

Distribution is a set of configuration files that define which components are used in this particular assistant.
This defines an assistant itself.

*(different Dream distributions may use different Annotators and Response Selectors, feature various Skills, and even speak different languages)*
- see how DeepPavlov Dream distribution works [here](https://docs.dream.deeppavlov.ai/dream_scheme.png)
- for full list of available distributions, click [here](https://docs.dream.deeppavlov.ai/ref_materials/distributions)

## Description
This particular DeepPavlov Dream distribution is powered by [Custom Knowledge Graph](https://docs.dream.deeppavlov.ai/ref_materials/custom_kg) option.
It is a tool for collecting, organising and storing data that can be used in any Dream Skill to offer the user a personalized experience and make bot replies more relevant.


## Services used in this DeepPavlov Dream Distribution
- sentence-ranker
- sentseg
- ranking-based-response-selector 
- ner
- entity-linking
- combined-classification
- entity-detection
- property-extraction
- custom-entity-linking
- terminusdb-server
- user-knowledge-memorizer
- dff-user-kg-skill
- dff-travel-italy-skill

