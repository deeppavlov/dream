#!/usr/bin/env bash

pip install gdown
if (! test -f model.meta) then
  gdown --id 1FCwO71TJha-d_kw3NkIgBUSicEOweyeh --output model.meta
fi

if (! test -f model.data-00000-of-00001) then
  gdown --id 1ALX6ahR8E-4QScQuS0wUxOalZdESBWNz --output model.data-00000-of-00001
fi
