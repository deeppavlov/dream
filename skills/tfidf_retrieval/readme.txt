Making dialog list: ./tfidf_dialog.sh

(You might need to uncomment last string in this file if you want to make the dialog list for Cobot).

If you set TFIDF_BAD_FILTER=1 in env, the phrase list will not only be formed from the good dialogs, but also phrases which are relatively more frequent in the bad dialogs will be discarded
If you don't want it, set TFIDF_BAD_FILTER=''
If you set USE_TFIDF_COBOT=1 ( and assuming dialog list for Cobot was already made), the phrase list will be formed from the positive Cobot output, not from the positive dialogs.

Custom dialogs need to be added into data/custom_dialog_list.json
Vectorizer was taken from the generative dialog skill which was developed before. The vectorizer was fitted on topicalchat, personachat and wizard of wikipedia, but not on the dialog test set.
