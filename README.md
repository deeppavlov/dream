# DeepPavlov Dream

**DeepPavlov Dream** is a platform for creating multi-skill chatbots.

To get architecture documentation, please refer to DeepPavlov Agent [readthedocs documentation](https://deeppavlov-agent.readthedocs.io).


# Distributions

We've already included two distributions: Deepy and a full-sized Dream chatbot.


# Quick Start

### Deploying via proxy
The easiest way to try out Dream is to deploy it via proxy.
This way all the requests will be redirected to DeepPavlov API, so you don't have to use any local resources.

1. Clone the repo

   ```git clone https://github.com/deepmipt/dream```


2. Install [docker](https://docs.docker.com/engine/install/) and [docker-compose](https://docs.docker.com/compose/install/) 

   If you get a "Permission denied" error running docker-compose, make sure to [configure your docker user](https://docs.docker.com/engine/install/linux-postinstall/) correctly.


3. Run

   ```docker-compose -f docker-compose.yml -f dev.yml -f proxy.yml up --build```

   - `docker-compose.yml` is your main deployment configuration;

   - `dev.yml` includes volume bindings for easier debugging;

   - `proxy.yml` is a list of proxied containers. See [proxy usage](#proxy-usage).


### Deploying components locally

Any components included in `docker-compose.yml` and not included in `proxy.yml` will be deployed locally.
Depending on your needs, you can:
   - Run ```docker-compose up --build``` to deploy everything on your machine.
   - Remove the components you need to deploy locally from `proxy.yml` and run
   
      ```docker-compose -f docker-compose.yml -f proxy.yml up --build```.

**Please note, that DeepPavlov Dream components require a lot of resources.**
Refer to the [components](#components) section to see estimated requirements for each component.



# Proxy usage

If your deployment resources are limited, you can replace containers with their proxied copies hosted by DeepPavlov.
To do this, override those container definitions inside `proxy.yml`, e.g.:
```
convers-evaluator-annotator:
  command: ["nginx", "-g", "daemon off;"]
  build:
    context: dp/proxy/
    dockerfile: Dockerfile
  environment:
    - PROXY_PASS=lnsigo.mipt.ru:8004
    - PORT=8004
```
and include this config in your deployment command:
```
docker-compose -f docker-compose.yml -f proxy.yml up --build
```
By default, `proxy.yml` contains all available proxy definitions.


# Components
## Annotators

| Name                        | Requirements | Description                                                                                                                                                                                                                     |
|-----------------------------|--------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------| 
| ASR                         | req          | calculates overall ASR confidence for a given utterance and grades it as either a very low, low, medium, or high (for Amazon markup)                                                                                            |
| Badlisted words             | req          | detects words and phrases from the badlist                                                                                                                                                                                      |
| Combined classification     | req          | BERT-based model including topic classification, dialog acts classication, sentiment, toxicity, emotion, factoid classifcation                                                                                                  |
| COMeT                       | req          | Commonsense prediction models COMeT Atomic and ConceptNet                                                                                                                                                                       |
| Convers Evaluator Annotator | req          | is trained on the Alexa Prize data from previous competitions and predicts whether candidate response is interesting, comprehensible, on-topic, engaging, and erroneous                                                         |
| Entity detection            | req          | extracts entities and their types from utterances                                                                                                                                                                               |
| Entity linking              | req          | finds Wikidata entity ids for the entities detected with Entity Detection                                                                                                                                                       |
| Entity Storer               | req          | a rule-based component, which extracts from the user's and socialbot's utterances entities if opinion expression is detected with patterns or MIDAS Classifier and saves them along with the detected attitude to dialogue state |
| Fact random                 | req          | returns random facts for the given entity (for entities from user utterance)                                                                                                                                                    |
| Fact retrieval              | req          | extracts facts from Wikipedia and wikiHow                                                                                                                                                                                       |
| Intent catcher              | req          | classifies user utterances into a number of predefined intents which are trained on a set of phrases and regexps                                                                                                                |
| KBQA                        | req          | answers user's factoid questions based on Wikidata KB                                                                                                                                                                           |
| MIDAS classification        | req          | BERT-based model trained on a semantic classes subset of MIDAS dataset                                                                                                                                                          |
| NER                         | req          | extracts person names, names of locations, organizations from the uncased text                                                                                                                                                  |
| News API annotator          | req          | extracts the latest news about entities or topics using the GNews API. For Dream on our resources we utilize our own API key.                                                                                                   |
| Sentrewrite                 | req          | rewrites the user's utterances by replacing pronouns with specific names that provide more useful information to downstream components                                                                                          |
| Sentseg                     | req          | allows us to handle long and complex user's utterances by punctuation recovery and splitting them into sentences                                                                                                                |
| Spacy nounphrases           | req          | extracts nounphrases using Spacy, and filters too simple ones                                                                                                                                                                   |
| Speech Function Classifier  | req          | a hierarchical algorithm based on several linear models and a rule-based approach for the prediction of speech functions described by Eggins and Slade                                                                          |
| Speech Function Predictor   | req          | yields probabilities of speech functions that can follow a speech function predicted by Speech Function Classifier                                                                                                              |
| Spelling preprocessing      | req          | pattern-based component to rewrite different colloquial expressions to a more formal style of conversation                                                                                                                      |
| Topic recommendation        | req          | offers a topic for further conversation using the information about the discussed topics and user's preferences. Current version is based on Reddit personalities (see Dream Report for Alexa Prize 4).                         |
| User Persona Extractor      | req          | determines which age category the user belongs to based on some key words                                                                                                                                                   |
| Wiki parser                 | req          | extracts Wikidata triplets for the entities detected with Entity Linking                                                                                                                                                        |

## Skills
| Name                      | Requirements | Description                                                                                                                                                                                            |
|---------------------------| --- |--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------| 
| Christmas Skill           | req | supports FAQ , facts, and scripts for Christmas                                                                                                                                                        |
| Comet Dialog skill        | req | uses COMeT ConceptNet model to express an opinion, to ask a question or give a comment about user's actions mentioned in the dialogue                                                                  |
| Convert Reddit            | req | uses a ConveRT encoder to build efficient representations for sentences                                                                                                                                |
| Dummy Skill               | req | a fallback skill with multiple non-toxic candidate responses                                                                                                                                           |
| Dummy Skill Dialog        | req | returns the next turn from the Topical Chat dataset if the response of the user to the Dummy Skill is similar to the corresponding response in the source data                                         |
| Eliza                     | req | Chatbot (https://github.com/wadetb/eliza)                                                                                                                                                              |
| Emotion skill             | req | returns template responses to emotions detected by the Emotion Classification from Combined Classsification annotator                                                                                  |
| Factoid QA                | req | answers factoid questions                                                                                                                                                                              |
| Game Cooperative skill    | req | provides user with a conversation about computer games: the charts of the best games for the past year, past month, and last week                                                                      |
| Intent Responder          | req | provides template-based replies for some of the intents detected by Intent Catcher annotator                                                                                                           |
| Knowledge Grounding skill | req | generates a response based on the dialogue history and provided knowledge related to the current conversation topic                                                                                    |
| Meta Script skill         | req | provides a multi-turn dialogue around  human activities. The skill uses COMeT Atomic model to generate common sense descriptions and questions on several aspects                                      |
| Misheard ASR              | req | uses the ASR Processor annotations to give feedback to the user when ASR confidence is too low                                                                                                         |
| News API skill            | req | presents the top-rated latest news about entities or topics using the GNews API                                                                                                                        |
| Oscar Skill               | req | supports FAQ , facts, and scripts for Oscar                                                                                                                                                            |
| Personal Info skill       | req | queries and stores user's name, birthplace, and location                                                                                                                                               |
| Personality Catcher       | req | desc                                                                                                                                                                                                   |
| Program Y                 | req | **[New DFF version]** Chatbot Program Y (https://github.com/keiffster/program-y) adapted for Dream socialbot                                                                                                                 |
| Program Y Dangerous       | req | **[New DFF version]** Chatbot Program Y (https://github.com/keiffster/program-y) adapted for Dream socialbot, containing responses to dangerous situations in a dialog                                                       |
| Program Y Wide            | req | **[New DFF version]** Chatbot Program Y (https://github.com/keiffster/program-y) adapted for Dream socialbot, and including only very general templates (with lower confidence)                                              |
| Small Talk skill          | req | asks questions using the hand-written scripts for 25 topics, including but not limited to love, sports, work, pets, etc.                                                                               |
| SuperBowl Skill           | req | supports FAQ , facts, and scripts for SuperBowl                                                                                                                                                        |
| Valentine's Day Skill     | req | supports FAQ , facts, and scripts for Valentine's Day                                                                                                                                                  |
| Wikidata Dial Skill       | req | generates an utterance using Wikidata triplets. Not turned on, needs improvement                                                                                                                       |
| DFF Animals skill         | req | is created using DFF and has three branches of conversation about animals: user's pets, pets of the socialbot, and wild animals                                                                        |
| DFF Art skill             | req | DFF-based skill to discuss art                                                                                                                                                                         |
| DFF Book skill            | req | **[New DFF version]** detects book titles and authors mentioned in the user's utterance with the help of the Wiki parser and Entity linking and recommends books by leveraging information from the GoodReads database       |
| DFF Bot Persona skill     | req | aims to discuss user favorites and 20 most popular things with short stories expressing the socialbot's opinion towards them                                                                           |
| DFF Coronavirus skill     | req | **[New DFF version]** retrieves data about the number of coronavirus cases and deaths in different locations from the sources of the John Hopkins University Center for System Science and Engineering |
| DFF Food skill            | req | constructed with DFF to encourage food-related conversation                                                                                                                                            |
| DFF Friendship skill      | req | DFF-based skill to greet the user in the beginning of the dialog, and forward the user to some scripted skill                                                                                          |
| DFF Funfact skill         | req | **[New DFF version]** constructed with DFF to tell user fun facts when one asked for them                                                                                                              |
| DFF Gaming skill          | req | provides video games discussion,   Gaming Skill is for more general talk about video games                                                                                                             |
| DFF Gossip skill          | req | DFF-based skill to discus persons with news about them                                                                                                                                                 |
| DFF Grounding skill       | req | **[New DFF version]** DFF-based skill to answer what is the topic of the conversation, to generate acknowledgement, to generate universal responses on some dialog acts by MIDAS                       |
| DFF Movie skill           | req | is implemented using DFF and takes care of the conversations related to movies                                                                                                                         |
| DFF Music skill           | req | DFF-based skill to discuss music                                                                                                                                                                       |
| DFF Science skill         | req | DFF-based skill to discuss science                                                                                                                                                                     |
| DFF Short Story skill     | req | **[New DFF version]** tells user short stories from 3 categories: (1) bedtime stories, such as fables and moral stories, (2) horror stories, and (3) funny ones                                                              |
| DFF Sports Skill          | req | DFF-based skill to discuss sports                                                                                                                                                                      |
| DFF Travel skill          | req | DFF-based skill to discuss travel                                                                                                                                                                      |
| DFF Weather skill         | req | **[New DFF version]** uses the OpenWeatherMap service to get the forecast for the user's location                                                                                                                            |
| DFF Wiki skill            | req | used for making scenarios with the extraction of entities, slot filling, facts insertion, and acknowledgments                                                                                          |

# Papers
### Alexa Prize 3
[Kuratov Y. et al. DREAM technical report for the Alexa Prize 2019 //Alexa Prize Proceedings. – 2020.](https://m.media-amazon.com/images/G/01/mobile-apps/dex/alexa/alexaprize/assets/challenge3/proceedings/Moscow-DREAM.pdf)

### Alexa Prize 4
[Baymurzina D. et al. DREAM Technical Report for the Alexa Prize 4 //Alexa Prize Proceedings. – 2021.](https://d7qzviu3xw2xc.cloudfront.net/alexa/alexaprize/docs/sgc4/MIPT-DREAM.pdf)


# License

DeepPavlov Dream is licensed under Apache 2.0.


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