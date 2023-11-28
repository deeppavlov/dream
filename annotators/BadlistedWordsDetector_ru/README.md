# BadlistedWordsDetector for Russian

## Description

Spacy-based user utterance annotator that detects words and phrases from the badlist.

This version of the annotator works for the Russian Language.

## I/O
**Input:**
Takes a list of user's utterances
```
["не пизди.", "застрахуйте уже его", "пошел нахер!"]
```

**Output:**
Returns words and their tags
```
[{"bad_words": True}, {"bad_words": False}, {"bad_words": True}]
```

## Dependencies
none