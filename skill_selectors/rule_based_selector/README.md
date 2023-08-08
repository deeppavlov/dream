# Rule-based Skill Selector

## Description

Skill Selector is a component selecting a subset of skills to generate hypotheses.
The Rule-based Skill Selector utilizes hand-written rules based on user's utterance annotations
(e.g., entities, dialog acts, intents, topics, toxicity, etc.).
Best fit for Dream Scripted, Dream Alexa distributions and other ones containing a lot of scripted skills.
Not suitable for prompt-based distributions.

### Parameters

```
HIGH_PRIORITY_INTENTS: whether to turn on only Intent Responder for high-priority intents
RESTRICTION_FOR_SENSITIVE_CASE: whether to use restrictions (e.g., no generative skills) for sensitive topics (e.g., religion or politics)
ALWAYS_TURN_ON_ALL_SKILLS: whether to always turn on all skills. Avoid using this parameter, it is more for debug purposes
```

## Dependencies
