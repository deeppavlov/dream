This model is based on the transformer-agnostic multitask neural architecture. 
It can solve several tasks similtaneously, almost as good as single-task models.
The models were trained on the following datasets:
Factoid classification : For the Factoid task, we used the same Yahoo ConversVsInfo dataset that was used to train the Dream socialbot in Alexa Prize . Note that the valid set in this task was equal to the test set. 
Midas classification : For the Midas task, we used the same Midas classification dataset that was used to train the Dream socialbot in Alexa Prize . Note that the valid set in this task was equal to the test set. 
Emotion classification :For the Emotion classification task, we used the emo_go_emotions dataset, with all the 28 classes compressed into the seven basic emotions as in the original paper. Note that these 7 emotions are not exactly the same as the 7 emotions in the original Dream socialbot in Alexa Prize: 1 emotion differs (love VS disgust), so the scores are incomparable with the original model. Note that this task is multiclass. 
Topic classification: For the Topic classification task, we used the dataset made by Dilyara Zharikova. The dataset was further filtered and improved for the final model version, to make the model suitable for DREAM.
Note that the original topics model doesnt account for that dataset changes(which were also about class number) and thus its scores are not compatible with the scores we have
Sentiment classification : For the Sentiment classification task, we used the Dynabench dataset (r1 + r2). 
Toxic classification : For the toxic classification task, we used the dataset from kaggle https://www.kaggle.com/competitions/jigsaw-unintended-bias-in-toxicity-classification/datawith the 7 toxic classes that pose an interest to us. Note that this task is multiclass.
The models (multitask and comparative single task) were trained with initial learning rate 2e-5(with validation patience 2 it could be dropped 2 times), batch size 32,optimizer adamw(betas (0.9,0.99) and early stop on 3 epochs. The criteria on early stopping was average accuracy for all tasks for multitask models, or the single-task accuracy for singletask models. 
Here are the model scores. Note that scores fo

| model                                  | factoid  (acc/f1) | sentiment (acc/f1) | midas (acc/f1) | emotion (acc/f1) | toxic(acc/f1) | topics (acc/f1) |
|----------------------------------------|-------------------|--------------------|----------------|------------------|---------------|-----------------|
| singletask, distilbert base uncased    | 83.05/83.02       | 74.45/74.23        | 81.71/81.36    | 61.21/68.07      | 91.54/61.95   | 79.82/79.75     |
| **multitask, distilbert base uncased** |                   |                    |                |                  |               |                 |
| singletask, bert base uncased          | 84.07/84.02       | 76.28/76.24        | 82.46/82.34    | 60.62/66.52      | 93.59/67.69   | 80.3/80.25      |
| multitask, bert base uncased           |                   |                    |                |                  |               |                 |
| source models, bert base uncased       | 86.44/86.27       | 76.94/             | /79.28         | /64              | to eval       | incompatible    |

