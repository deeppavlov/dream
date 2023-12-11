# ASR : Automatic Speech Recognition

## Description

ASR component allows users to provide speech input via its `http://_service_name_:4343/asr?user_id=` endpoint.  To do so, attach the recorded voice as a `.wav` file, 16KHz. 

## I/O
**Input:** 
user utterance: recorded voice as a `.wav` file

**Output** 
asr_confidence: a probability of a user speech recognition 


## Dependencies
none

