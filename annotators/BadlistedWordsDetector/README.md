# BadlistedWordsDetector

## Description
Spacy-based user utterance annotator that detects words and phrases from the badlist

## I/O
**Input:** a list of user's utterances
```
["fucking hell", "he mishit the shot", "you asshole"]
```

**Output:** words and their tags
```
 [{"bad_words": True}, {"bad_words": False}, {"bad_words": True}]
```


## Dependencies
none