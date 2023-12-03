# Custom Entity Linking

## Description
This component is an Annotator that sematically links entities detected in user utterances. Entites then bound via relations.

Relation examples:
- `favorite animal`
- `like animal`
- `favorite book`
- `like read`
- `favorite movie`
- `favorite food`
- `like food`
- `favorite drink`
- `like drink`
- `favorite sport`
- `like sports`


## I/O

**Input**
Takes a list of user_id, entity substring, entity_tags

An input example:
```
"user_id": [user_id],
            "entity_substr": [entity_substr_list],
            "entity_tags": [entity_tags_list],
            "context": [context],
            "property_extraction": [property_extraction],
        }
```

**Output:**
- List of entity substrings (entity names).
- List of entity IDs.
- List of confidences.
- List of entity ID tags (entity kinds).
- List of property extraction information.
- List of preprocessed conversation



## Dependencies
- annotators.ner
- annotators.entity_detection
- annotators.spacy_nounphrases
