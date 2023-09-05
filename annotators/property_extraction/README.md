# Property Extraction

## Description

The Property Extraction annotator extracts user attributes in RDF-triplet format for a specific individual. This enables a dialog assistant to acquire information about the user’s preferred film, dish, location, etc., and utilize this knowledge to generate personalized responses.

The annotator is capable of extracting multiple user attributes from utterances in the form of (subject, predicate, object) triplets. The subject is designated as “user,” the relation represents the attribute name, and the object denotes the attribute value. There are 61 distinct relation types that the annotator currently supports, as listed in the rel_list.txt file.

Property Extraction annotator consists of the following components:

Relation classifier - a BERT-based model that finds all the user attributes in the current utterance, if there are any.
Entity generator - a se2seq model which generates the subject and object for each attribute found in the previuos step.


## I/O

**Input example**

```python
import requests

utterances = [["I love going for a walk with my two dogs every day."], ["I like travelling in Italy with my husband. And you?"]]
requests.post("http://0.0.0.0:8136/respond", json = {"utterances": utterances}).json()

>>> [
    {"triplets": [{"subject": "user", "relation": "like activity", "object": "walking"}, {"subject": "user", "relation": "have pet", "object": "two dogs"}]}, 
    {"triplets": [{"subject": "user", "property": "marital status", "object": "husband"}, {"subject": "user", "relation": "like activity", "object": "travel"}]}
    ]
```
