#!/usr/bin/env bash
python3 ./utils/download_and_write.py \
    --host=$DB_HOST \
    --port=$DB_PORT \
    --name=$DB_NAME \
    --delta=1 \
    --path_to_save=$S3_DIALOGS_BUCKET \
    --upload_to_s3
    
