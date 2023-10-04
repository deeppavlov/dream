# Description-based Skill Selector

## Description

Skill Selector is a component selecting a subset of skills to generate hypotheses.
The Description-based Skill Selector turns on  prompt-based skills (containing `prompted_skill` in their names)
which prompts where selected by Prompt Selector as the most relevant to the current context. 
The number of such prompts (thus, skills) is defined in Prompt Selector.
The Description-based Skill Selector also turns on skills Factoid QA (`factoid_qa`) 
and Google API Skill (`dff_google_api_skill`) to answer factoid questions,
and LLM-based Q&A on Documents Skill (`dff_document_qa_llm_skill`) when the bot attributes in the dialog state
contain the considered document(s).
All other skills from `pipeline_conf.json` (skills section) are turned on always. 

One does not need to change code of Description-based Skill Selector, when adding prompt-based skills. 
Otherwise, feel free to customize adding your own rules or other not prompt-based skills.

### Parameters

```
HIGH_PRIORITY_INTENTS: whether to turn on only Intent Responder for high-priority intents
RESTRICTION_FOR_SENSITIVE_CASE: whether to use restrictions (e.g., no generative skills) for sensitive topics (e.g., religion or politics)
ALWAYS_TURN_ON_ALL_SKILLS: whether to always turn on all skills. Avoid using this parameter, it is more for debug purposes
```

## Dependencies

- Prompt Selector annotations. If not provided, Skill Selector turns on all prompt-based skills from `pipeline_conf.json` (skills section).