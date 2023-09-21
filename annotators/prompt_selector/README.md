# Prompt selector


## Description

An annotator that utilizes Sentence Ranker to find the most relevant to the current context sentences from the bot's persona description.

The number of returned sentences is given as an environmental variable using `N_SENTENCES_TO_RETURN` in `docker-compose.yml`.

Selects among the prompts for which the prompted skills are included in the current pipeline.

## I/O



## Dependencies

