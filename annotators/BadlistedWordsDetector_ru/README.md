# BadlistedWordsDetector for Russian

## Description
component_type: annotator
is_customizable: true

Spacy-based user utterance annotator that detects words and phrases from the badlist. This version of the annotator works for the Russian Language.

## I/O
**Input:** a list of user's uttetances 
**Output:** words and their tags (`{"bad_words": False}` or `{"bad_words": True}`)

## Dependencies
none