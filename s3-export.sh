#!/bin/bash

export AWS_ACCESS_KEY_ID='AKIAT2RXIFYZLDB66LZ3'
export AWS_SECRET_ACCESS_KEY='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'
export AWS_DEFAULT_REGION='us-east-1'


aws s3 cp /home/export/deeppavlov_data s3://team-dream-storage/deeppavlov_data \
  --recursive \
  --acl=public-read \
  --exclude="*" \
  --include="classifiers/toxic_float_conv_bert_v0.tar.gz" \
  --include="bert/conversational_cased_L-12_H-768_A-12.tar.gz" \
  --include="classifiers/yahoo_convers_vs_info_v4.tar.gz" \
  --include="classifiers/sentiment_sst_bert_v2.tar.gz" \
  --include="wiki_index.tar.gz"

aws s3 cp /home/export/alexaprize_data s3://team-dream-storage/alexaprize_data \
  --recursive \
  --acl=public-read \
  --exclude="*" \
  --include="comet/atomic_pretrained_model.pickle" \
  --include="comet/categories_oEffect#oReact#oWant#xAttr#xEffect#xIntent#xNeed#xReact#xWant-maxe1_17-maxe2_35-maxr_1.pickle" \
  --include="conceptnet/conceptnet_pretrained_model.pickle" \
  --include="conceptnet/rel_language-trainsize_100-devversion_12-maxe1_10-maxe2_15-maxr_5.pickle" \
  --include="convert_reddit_v2.8.tar.gz" \
  --include="emo_bert3_v1.tar.gz" \
  --include="elmo2.tar.gz" \
  --include="ner.tar.xz" \
  --include="ood_dbdc_torch_bert_v2.tar.gz" \
  --include="question_generator/model_24_0.94_37.23.pth"

aws s3 cp /home/export/kbqa s3://team-dream-storage/kbqa \
  --recursive \
  --acl=public-read \
  --exclude="*" \
  --include="wikidata/wiki_eng_files_no_el.tar.gz" \
  --include="wikidata/sparql_queries.json" \
  --include="templates_eng_compr.json" \
  --include="wikidata/kbqa_entity_linking_eng.tar.gz" \
  --include="wikidata/types_dict.pickle" \
  --include="wikidata/wikidata_lite.hdt" \
  --include="wikidata/wikidata_lite.hdt.index.v1-1"
