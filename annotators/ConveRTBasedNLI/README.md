This model is designed to solve the Natural Language Inference problem.

It consists of two parts:
* [ConveRT model](https://arxiv.org/abs/1911.03688) that vectorizes the data
* Custom model consisting from 4 linear layers

The model was trained on the **Stanford Natural Language Inference** (SNLI) corpus that contains human-written English sentence pairs with the labels entailment, contradiction, and neutral. 

Pre-trained model available [here](http://files.deeppavlov.ai/tmp/nli_model.tar.gz).

If you want to train a model from scratch, just omit TRAINED_MODEL_PATH input argument or set it to _None_.
