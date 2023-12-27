# Personal Info Skill
## Description
A skill that is able to parse user's input and retrieve person's name.
## Input/Output

**Input**
Accepts annotated utterances, including NER
```
["my name is john."]
```
**Output**
A parsed utterance, retrieved name and a reply

```
 [["Nice to meet you, John."],
 ["text": "john", "type": "PER"]]
```

## Dependencies
none