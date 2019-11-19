#!/usr/bin/env bash

aws s3 cp s3://alexaprize/807746935730/conversation_feedback.csv .
aws s3 cp s3://alexaprize/807746935730/Ratings/ratings.csv .
aws s3 cp s3://alexaprize/807746935730/FrequentUtterances/FrequentUtterances_2019-10-10_2019-11-08.txt .
aws s3 cp s3://alexaprize/807746935730/ConversationAssessments/conversation_assessment_2019-11-09.csv . 