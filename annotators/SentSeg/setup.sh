#!/usr/bin/env bash

MODEL_META_URL=files.deeppavlov.ai/alexaprize_data/sentseg/model.meta
MODEL_DATA_URL=files.deeppavlov.ai/alexaprize_data/sentseg/model.data-00000-of-00001

if (! test -f model.meta) then
  curl $MODEL_META_URL > ./model.meta
fi

if (! test -f model.data-00000-of-00001) then
  curl $MODEL_DATA_URL > ./model.data-00000-of-00001
fi
