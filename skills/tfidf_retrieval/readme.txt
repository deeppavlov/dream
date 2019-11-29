Making dialog list: cd dp-agent-alexa/skills/tfidf_retrieval/data; python data_maker.py --ratings_file=MY_RATINGS_FILE --dialogs_file=MY_DIALOGS_FILE
Custom dialogs need to be added into data/custom_dialog_list.json
Vectorizer was taken from the generative dialog skill which was developed before. The vectorizer was fitted on topicalchat, personachat and wizard of wikipedia, but not on the dialog test set.
