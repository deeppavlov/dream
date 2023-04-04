# Components Multilingual Version

Dream Architecture is presented in the following image:
![DREAM](multilingualDREAM.png)

| Name                | Requirements | Description                                                                                                                                                                    |
|---------------------|--------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Rule Based Selector |              | Algorithm that selects list of skills to generate candidate responses to the current context based on topics, entities, emotions, toxicity, dialogue acts and dialogue history |
| Response Selector   | 50 MB RAM    | Algorithm that selects a final responses among the given list of candidate responses                                                                                           |

## Annotators

| Name                     | Requirements             | Description                                                                                                                                                    |
|--------------------------|--------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Sentiment Classification | 2 GB RAM, 2 GB GPU       | classifies sentiment to positive, negative and neutral classes                                                                                                 |
| Toxic Classification     | 3  GB RAM, 2 GB GPU      | classifies toxicity: identity_attack, insult, obscene, severe_toxicity, sexual_explicit, threat, toxicity                                                      |
| Sentence Ranker          | 2.5 GB RAM, 1.8 GB GPU   | for a pair of sentences predicts a floating point value. For multilingual version, return cosine similarity between embeddings from multilingual sentence BERT |

## Skills & Services
| Name               | Requirements          | Description                                                                                                                                       |
|--------------------|-----------------------|---------------------------------------------------------------------------------------------------------------------------------------------------|
| GPT-2 Multilingual | 5 GB RAM, 6.5 GB GPU  | GPT2-based generative model. For Multilingual distribution we propose mgpt by Sberbank [from HugginFace](https://huggingface.co/sberbank-ai/mGPT) |

# Papers

### Alexa Prize 3

[Kuratov Y. et al. DREAM technical report for the Alexa Prize 2019 //Alexa Prize Proceedings. – 2020.](https://m.media-amazon.com/images/G/01/mobile-apps/dex/alexa/alexaprize/assets/challenge3/proceedings/Moscow-DREAM.pdf)

### Alexa Prize 4

[Baymurzina D. et al. DREAM Technical Report for the Alexa Prize 4 //Alexa Prize Proceedings. – 2021.](https://d7qzviu3xw2xc.cloudfront.net/alexa/alexaprize/docs/sgc4/MIPT-DREAM.pdf)

# License

DeepPavlov Dream is licensed under Apache 2.0.

Program-y (see `dream/skills/dff_program_y_skill`, `dream/skills/dff_program_y_wide_skill`, `dream/skills/dff_program_y_dangerous_skill`)
is licensed under Apache 2.0.
Eliza (see `dream/skills/eliza`) is licensed under MIT License.

## Report creating

For making certification `xlsx` - file with bot responses, you can use `xlsx_responder.py` script by executing

```shell
docker-compose -f docker-compose.yml -f dev.yml exec -T -u $(id -u) agent python3 \
        utils/xlsx_responder.py --url http://0.0.0.0:4242 \
        --input 'tests/dream/test_questions.xlsx' \
        --output 'tests/dream/output/test_questions_output.xlsx'\
      --cache tests/dream/output/test_questions_output_$(date --iso-8601=seconds).json
```

Make sure all services are deployed. `--input` - `xlsx` file with certification questions, `--output` - `xlsx` file with bot responses, `--cache` - `json`, that contains a detailed markup and is used for a cache.
