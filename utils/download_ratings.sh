#!/usr/bin/env bash

echo "Downloading ratings, feedback, ..."
aws s3 cp --recursive s3://alexaprize/807746935730 ./ratings
echo "Done"