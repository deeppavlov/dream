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

**Inpunt**
user_id, entity substring, entity_tags

**Output:** 
processed information about:
- entities
- entity_id (ids for multiple entities)
- entity_confidence score
- entity_id_tags
  
## Dependencies
 annotators: `NER`, `entity_detection` and `spacy_nounphrases`
