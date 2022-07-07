
### Test User Samples
```
hi
i am good, do you like ocean?
what can you tell about ocean?
ocean is cool, do you like fishing
```

# Entity storer

Entity storer componenet is now used only for storing entities 
for which either human or bot expressed some attitude. 

The extraction of entities with attitude is in the function
`commnon.universal_templates.get_entities_with_attitudes` which is now fully based 
on regular expressions.

We also do not store extra information. Current entity dict is the following:
```python
"human_attributes": {
    "entities": {
        "apple": {
            "name": "apple",
            "human_encounters": [],
            "bot_encounters": [],
            "human_attitude": "like",
            "bot_attitude": null
        },
        "jewelry": {
            "name": "jewelry",
            "human_encounters": [],
            "bot_encounters": [
                {
                    "human_utterance_index": 6,
                    "full_name": "jewelry",
                    "skill_name": "dff_grounding_skill"
                }
            ],
            "human_attitude": null,
            "bot_attitude": "like"
        }
    }
}
```

One can find here the entities and the attitudes: `human_attitude` and `bot_attitude` for each entity.
The attitude is null if collocator have not given any opinion on the entity yet.