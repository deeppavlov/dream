# DeepPavlov Agent


**DeepPavlov Agent** is a platform for creating multi-skill chatbots.

Please refer to our [readthedocs documentation](https://deeppavlov-agent.readthedocs.io).

- [Alexa Bot README](README-alexa.md)
- Travis Tests Status on dev branch: [![Build Status](https://travis-ci.com/sld/dp-agent-alexa.svg?token=iYvsyXT3Gi1yjduLqC6t&branch=dev)](https://travis-ci.com/sld/dp-agent-alexa)
- Jenkins Tests Status on dev branch: [![Build Status](http://lnsigo.mipt.ru:8080/buildStatus/icon?job=assistant%2Fdev)](http://lnsigo.mipt.ru:8080/job/dp-multibranch/job/dev/)


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