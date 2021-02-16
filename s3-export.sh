#!/bin/bash

export AWS_ACCESS_KEY_ID='AKIAT2RXIFYZLDB66LZ3'
export AWS_SECRET_ACCESS_KEY='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'
export AWS_DEFAULT_REGION='us-east-1'

base=/home/export
bucket=team-dream-storage

files=(
  deeppavlov_data/classifiers/toxic_float_conv_bert_v0.tar.gz
  deeppavlov_data/bert/conversational_cased_L-12_H-768_A-12.tar.gz
  deeppavlov_data/classifiers/yahoo_convers_vs_info_v4.tar.gz
  deeppavlov_data/classifiers/sentiment_sst_bert_v2.tar.gz
  deeppavlov_data/wiki_index.tar.gz
  alexaprize_data/cobot_bert_6task.tar.gz
  alexaprize_data/comet/atomic_pretrained_model.pickle
  alexaprize_data/comet/categories_oEffect#oReact#oWant#xAttr#xEffect#xIntent#xNeed#xReact#xWant-maxe1_17-maxe2_35-maxr_1.pickle
  alexaprize_data/conceptnet/conceptnet_pretrained_model.pickle
  alexaprize_data/conceptnet/rel_language-trainsize_100-devversion_12-maxe1_10-maxe2_15-maxr_5.pickle
  alexaprize_data/convert_reddit_v2.8.tar.gz
  alexaprize_data/convert_reddit_v2.3.tar.gz
  alexaprize_data/emo_bert3_v1.tar.gz
  alexaprize_data/elmo2.tar.gz
  alexaprize_data/ner.tar.xz
  alexaprize_data/ood_dbdc_torch_bert_v2.tar.gz
  alexaprize_data/question_generator/model_24_0.94_37.23.pth
  kbqa/wikidata/wiki_eng_files_no_el.tar.gz
  kbqa/wikidata/sparql_queries.json
  kbqa/templates_eng_compr.json
  kbqa/wikidata/kbqa_entity_linking_eng.tar.gz
  kbqa/wikidata/types_dict.pickle
  kbqa/wikidata/wikidata_lite.hdt
  kbqa/wikidata/wikidata_lite.hdt.index.v1-1
)

for file in ${files[@]}; do
  aws s3api head-object --bucket $bucket --key $file || \
  aws s3 cp $base/$file s3://team-dream-storage/$file \
  --acl=public-read
done
