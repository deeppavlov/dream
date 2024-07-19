# DNNC intent classifier
## Description
Classifier that classifies DNNC intent in the few-shot mode. Default version is the logistic regression. Howeve, with config classifier_roberta.json  entailment-trained roberta is also supported
## Input/Output
**Input**
Batch of last utterances
**Output**
For each utterance - dictionary {probable class: probability}
## Dependencies
As stated in requirements.txt. And if you use entailment-trained roberta, file utils_roberta.py also is useful
