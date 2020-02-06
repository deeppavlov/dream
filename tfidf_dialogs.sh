mkdir dialog_data
aws s3 cp --recursive s3://alexa-prod-dialogs-dumps dialog_data
aws s3 cp s3://alexaprize/807746935730/Ratings/ratings.csv ./ratings/
python3 skills/tfidf_retrieval/data/json_concat.py --dialogs_dir=dialog_data --output_file=dialogs
rm -r dialog_data
python3 skills/tfidf_retrieval/data/data_maker.py --ratings_file=ratings/ratings.csv --dialogs_file=dialogs --output_file=skills/tfidf_retrieval/data/dialog_list_v1.json --bad_output_file=skills/tfidf_retrieval/data/bad_dialog_list_v1.json --assessment_file=skills/tfidf_retrieval/data/conversation_assessment.csv --good_poor_phrase_file=skills/tfidf_retrieval/data/goodpoor.json
#python3 skills/tfidf_retrieval/data/cobot_data_maker.py --dialogs_file=dialogs --output_file=skills/tfidf_retrieval/data/cobot_dialog_list.json
