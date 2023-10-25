# ASR : Automatic Speech Recognition

## Description
component_type: annotator
is_customizable: true

ASR component allows users to provide speech input via its `http://_service_name_:4343/asr?user_id=` endpoint.  To do so, attach the recorded voice as a `.wav` file, 16KHz. 

This component calculates overall ASR confidence for a given utterance and grades it as either *very low*, *low*, *medium*, *high* or *undefined* (for Amazon markup).

## I/O
**Input:** 
user utterance: recorded voice as a `.wav` file

**Output** 
asr_confidence: a probability of a user speech recognition 


## Dependencies
none

