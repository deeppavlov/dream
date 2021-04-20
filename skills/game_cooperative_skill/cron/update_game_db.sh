#!/bin/bash

cd "$(dirname "$0")"

source /root/.env

export AWS_ACCESS_KEY_ID='AKIAT2RXIFYZLDB66LZ3'
export AWS_SECRET_ACCESS_KEY='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'
export AWS_DEFAULT_REGION='us-east-1'

export bucket=team-dream-storage
export base_dir=game-cooperative-skill
export local_dir=/data/$base_dir
export local_file=$local_dir/game_db.json
export s3_file=$base_dir/$RAWG_API_KEY/game_db.json
export md_file=/tmp/meta_data.json


mkdir -p $local_dir

function db_update() {
    aws s3 cp $local_file s3://$bucket/$s3_file --acl=public-read
}

function db_load() {
    wget https://$bucket.s3.amazonaws.com/$s3_file -O ${local_file}|| return 1
}


function is_updated() {
    aws s3api head-object --bucket $bucket --key $s3_file > $md_file
    python is_updated.py -m $md_file || return 1
}

function random_wait() {
    sleep $(( $( shuf -i 0-59 -n 1 ) * $1 ))
}
if [ -z "$1" ]
then
    is_updated || { random_wait 60 ; is_updated || { python create_new_db.py -d $local_file && db_update; }; };
    db_load
else
    db_load || { random_wait 2 ; db_load || { python create_new_db.py -d $local_file && db_update; }; };
    db_load
fi