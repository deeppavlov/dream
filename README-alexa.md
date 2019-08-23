# Alexa skill based on DeepPavlov Agent

CoBotQA miniskill
========================
CoBotQA miniskill sends requests to CoBot's services. Two environment variables
should be set to use this miniskill:
 * COBOT_API_KEY - API key given to our Team
 * COBOT_QA_SERVICE_URL - service url, could be found in Trello

How to run and test
=======================

```
$: docker-compose -f docker-compose.yml -f skills.yml up --build
$: docker-compose -f docker-compose.yml -f skills.yml exec agent bash
$(inside docker): python3 -m core.run
```
