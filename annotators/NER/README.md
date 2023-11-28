# Title
Named Entity Recognition Annotator

## Description
Extracts people names, locations and names of organizations from an uncased text

## Input/Output

**Input**
A list of user utterances
```
["john peterson is my brother.", "he lives in New York."]
```


**Output**
A user utterance annotated by
- confidence level
- named entity's position in a sentence (`start_pos` and `end_pos`)
- the named the entity itself
- the named entity type

```
 [{"confidence": 1, "end_pos": 5, "start_pos": 3, "text": "New York", "type": "LOC"}],
```

## Dependencies
none