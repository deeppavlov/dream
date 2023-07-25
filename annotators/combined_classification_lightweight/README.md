This model is based on the transformer-agnostic multitask neural architecture. It can solve several tasks similtaneously, almost as good as single-task models. 

The models were trained on the following datasets:

**Factoid classification** : For the Factoid task, we used the same Yahoo ConversVsInfo dataset that was used to train the Dream socialbot in Alexa Prize . Note that the valid set in this task was equal to the test set. 

**Midas classification** : For the Midas task, we used the same Midas classification dataset that was used to train the Dream socialbot in Alexa Prize . Note that the valid set in this task was equal to the test set. 

**Emotion classification** :For the Emotion classification task, we used the emo\_go\_emotions dataset, with all the 28 classes compressed into the seven basic emotions as in the original paper. Note that these 7 emotions are not exactly the same as the 7 emotions in the original Dream socialbot in Alexa Prize: 1 emotion differs (love VS disgust), so the scores are incomparable with the original model. Note that this task is multiclass. 

**Topic classification**: For the Topic classification task, we used the dataset made by Dilyara Zharikova. The dataset was further filtered and improved for the final model version, to make the model suitable for DREAM. Note that the original topics model doesn’t account for that dataset changes(which were also about class number) and thus its scores are not compatible with the scores we have.

**Sentiment classification** : For the Sentiment classification task, we used the Dynabench dataset (r1 + r2). 

**Toxic classification** : For the toxic classification task, we used the dataset from kaggle <https://www.kaggle.com/competitions/jigsaw-unintended-bias-in-toxicity-classification/datawith> the 7 toxic classes that pose an interest to us. Note that this task is multilabel.

The model also contains 3 replacement models for Amazon services.

The models (multitask and comparative single task) were trained with initial learning rate 2e-5(with validation patience 2 it could be dropped 2 times), batch size 32,optimizer adamW(betas (0.9,0.99) and early stop on 3 epochs. The criteria on early stopping was average accuracy for all tasks for multitask models, or the single-task accuracy for singletask models.

This model(with a huawei-noah/TinyBERT_General_4L_312D backbone) on a CPU-only inference takes 42% less time than combined_classification, while using only ~1.5 Gb of the CPU instead of the 2909 Mb for combined_classification. The average accuracy and average F1 at the same time are for this model only ~1.5% lower than for the combined_classification, and this dropdown is consistent for all tasks.


