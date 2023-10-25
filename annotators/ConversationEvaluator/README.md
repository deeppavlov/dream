# Conversation Evaluator

## Description
This annotator is trained on the Alexa Prize data from the previous competitions and predicts whether the candidate response is interesting, comprehensible, on-topic, engaging, or erroneous.

## Input/Output

**Input**
- possible assistant's replies
- user's past responses 
**Output**
tags 
- `isResponseComprehensible`
- `isResponseErroneous`
- `isResponseInteresting`
- `isResponseOnTopic`
- `responseEngagesUser`

with their probabilities

## Dependencies
none
