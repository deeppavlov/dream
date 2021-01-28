## Description

Intent Catcher. Each utterance is decomposed into sentences using sentseg, each sentence is embedded using an Universal sentence encoder (USE, https://arxiv.org/pdf/1803.11175.pdf).

## IMPORTANT:

As you **add new phrases to the intents**, please be very careful. Intents should not cross, as that would make a negative impact on the model. Don't add unclear/meaningless phrases where intent isn't clear, or where speech wasn't correctly transcribed - this would only make models's quality deteriorate.

## Getting started

To add new intent, you should
 1. Fit the model on the intents (look for example Colab notebook). \\
 2. Then add the model to models, modify config and run.

## Tests

The test sentences are contained in `tests.json` file. To run tests, run the intent\_catcher service and run `./test.sh`.
