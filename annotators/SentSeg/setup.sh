#!/usr/bin/env bash

pip install gdown
if (! test -f model.meta) then
  gdown --id 1rtmaUipUqQbAKfzL7LoawdFjRLN9gRKn --output model.meta
fi

if (! test -f model.data-00000-of-00001) then
  gdown --id 1a7Q1eHpKWnj5isaRIR6HjIydR-lO5mpq --output model.data-00000-of-00001
fi
