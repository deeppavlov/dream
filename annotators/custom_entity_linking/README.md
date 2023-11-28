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
```

**Output:**
processed information about:
- entities
- entity_id (ids for multiple entities)
- entity_confidence score
- entity_id_tags

An output example:
```
```

## Dependencies
- annotators.ner
- annotators.entity_detection
- annotators.spacy_nounphrases
