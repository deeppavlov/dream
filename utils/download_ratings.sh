#!/usr/bin/env bash

echo "Downloading ratings"
aws s3 cp s3://alexaprize/807746935730/conversation_feedback.csv ./ratings/
aws s3 cp s3://alexaprize/807746935730/Ratings/ratings.csv ./ratings/

echo "Downloading conversation assessment"
python utils/download_conversation_assessment.py

echo "Downloading frequent utterances"
python utils/download_frequent_utterances.py

echo "Done"