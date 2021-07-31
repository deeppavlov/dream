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
  deeppavlov_data/bert/uncased_L-4_H-128_A-2.zip
  deeppavlov_data/wiki_index.tar.gz
  deeppavlov_data/multi_squad_model_noans_1.1.tar.gz
  alexaprize_data/cobot_bert_6task.tar.gz
  alexaprize_data/comet/atomic_pretrained_model.pickle
  alexaprize_data/comet/categories_oEffect#oReact#oWant#xAttr#xEffect#xIntent#xNeed#xReact#xWant-maxe1_17-maxe2_35-maxr_1.pickle
  alexaprize_data/conceptnet/conceptnet_pretrained_model.pickle
  alexaprize_data/conceptnet/rel_language-trainsize_100-devversion_12-maxe1_10-maxe2_15-maxr_5.pickle
  alexaprize_data/convert_reddit_v2.8.tar.gz
  alexaprize_data/convert_reddit_v2.3.tar.gz
  alexaprize_data/convert_reddit_v2.3.punct.tar.gz
  alexaprize_data/book_query_dict.pkl
  alexaprize_data/emo_bert3_v1.tar.gz
  alexaprize_data/elmo2.tar.gz
  alexaprize_data/midas_conv_bert_v2.tar.gz
  alexaprize_data/ner.tar.xz
  deeppavlov_data/classifiers/ood_dbdc_bert_v1.tar.gz
  deeppavlov_data/bert/uncased_L-12_H-768_A-12.zip
  alexaprize_data/question_generator/model_24_0.94_37.23.pth
  kbqa/wikidata/wiki_eng_files_no_el.tar.gz
  kbqa/wikidata/sparql_queries.json
  kbqa/templates_eng_compr.json
  kbqa/wikidata/kbqa_entity_linking_eng.tar.gz
  kbqa/wikidata/types_dict.pickle
  kbqa/wikidata/q_to_par_en.pickle
  kbqa/wikidata/wikidata_lite.hdt
  kbqa/wikidata/wikidata_lite.hdt.index.v1-1
  kbqa/models/rel_ranking.tar.gz
  kbqa/wikidata/topical_chat.tar.gz
  kbqa/wikidata/wiki_dict_properties.pickle
  embeddings/reddit_fastText/wordpunct_tok_reddit_comments_2017_11_100.bin
  kbqa/wikidata/path_ranking_data.tar.gz
  kbqa/models/opendialkg_path_ranking_lite.tar.gz
  kbqa/models/dialogpt_wiki.tar.gz
  kbqa/models/fact_ranking_bert_lite.tar.gz
  kbqa/models/rel_ranking_bert_lite.tar.gz
  datasets/wikipedia/enwiki_lite.tar.gz
  kbqa/wikidata/topical_chat.tar.gz
  kbqa/wikidata/q_to_descr_en.pickle
  kbqa/wikidata/q_to_page_en.pickle
  kbqa/wikidata/wikidata_cache.json
  alexaprize_data/database_most_popular_main_info_v1.json
  datasets/wikipedia/enwiki_latest.db
  alexaprize_data/logreg_recommendation_model.pkl
  datasets/wikipedia/enwiki_latest_hyperlinks.db
  kbqa/wikidata/wikihow.pickle
  kbqa/wikidata/breed_facts.json
  kbqa/wikidata/wikihow.db
  kbqa/wikidata/wikihow_topics.json
  alexaprize_data/parlai_grounding_knowledge/parlai_topical_chat_data.tar.gz
  alexaprize_data/parlai_grounding_knowledge/topical_chat_blender90_1_sent_48_epochs.tar.gz
  alexaprize_data/parlai_grounding_knowledge/topical_chat_blender90_3_sent_62_epochs.tar.gz
  alexaprize_data/dummy_skill_dialog.tar.gz
  kbqa/wikidata/entity_types_sets.pickle
  datasets/wikipedia/enwiki_latest_topic.db
  alexaprize_data/movie_plots_v0.tar.gz
  alexaprize_data/reddit_embeddings.pickle
  deeppavlov_data/dialog_entity_detection/dialog_entity_detection_model.tar.gz
  deeppavlov_data/dialog_entity_detection/bert-base-uncased.tar.gz
)

for file in ${files[@]}; do
  aws s3api head-object --bucket $bucket --key $file || \
  aws s3 cp $base/$file s3://team-dream-storage/$file \
  --acl=public-read
  aws s3 cp $base/$file.md5 s3://team-dream-storage/$file.md5 \
  --acl=public-read
done
