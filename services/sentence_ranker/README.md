# Sentence Ranker Service

This is a universal service for evaluation of a sentence pair.

The model can be selected from HugginFace library and passed as a `PRETRAINED_MODEL_NAME_OR_PATH` parameter.

The service accepts a batch of sentence pairs (a pair is a list of two strings), and returns a batch of floating point values. 

To rank a list of sentence pairs, one can get floating point values for each pair and maximize the value.
