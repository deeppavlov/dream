wget Docker-ExternalLoa-LOFSURITNPLE-525614984.us-east-1.elb.amazonaws.com:4242/dialogs -O dialogs
aws s3 cp s3://alexaprize/807746935730/Ratings/ratings.csv ./ratings/
python3 skills/tfidf_retrieval/data/data_maker.py --ratings_file=ratings/ratings.csv --dialogs_file=dialogs --output_file=skills/tfidf_retrieval/data/dialog_list.json --bad_output_file=skills/tfidf_retrieval/data/bad_dialog_list.json --assessment_file=skills/tfidf_retrieval/data/conversation_assessment.csv
#python3 skills/tfidf_retrieval/data/cobot_data_maker.py --dialogs_file=dialogs --output_file=skills/tfidf_retrieval/data/cobot_dialog_list.json
