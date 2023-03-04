# DeepPavlov Dream

**DeepPavlov Dream** is a platform for creating multi-skill chatbots.

To get architecture documentation, please refer to DeepPavlov Agent [readthedocs documentation](https://deeppavlov-agent.readthedocs.io).

# Distributions

We've already included six distributions: four of them are based on lightweight Deepy socialbot,
one is a full-sized Dream chatbot (based on Alexa Prize Challenge version) in English and a Dream chatbot in Russian.

### Deepy Base

Base version of Lunar assistant.
Deepy Base contains Spelling Preprocessing annotator,
template-based Harvesters Maintenance Skill,
and AIML-based open-domain Program-y Skill based on Dialog Flow Framework.

### Deepy Advanced

Advanced version of Lunar assistant.
Deepy Advanced contains Spelling Preprocessing, Sentence Segmentation,
Entity Linking and Intent Catcher annotators, Harvesters Maintenance GoBot Skill for goal-oriented responses,
and AIML-based open-domain Program-y Skill based on Dialog Flow Framework.

### Deepy FAQ

FAQ version of Lunar assistant.
Deepy FAQ contains Spelling Preprocessing annotator,
template-based Frequently Asked Questions Skill,
and AIML-based open-domain Program-y Skill based on Dialog Flow Framework.

### Deepy GoBot

Goal-oriented version of Lunar assistant.
Deepy GoBot Base contains Spelling Preprocessing annotator,
Harvesters Maintenance GoBot Skill for goal-oriented responses,
and AIML-based open-domain Program-y Skill based on Dialog Flow Framework.

### Dream

Full version of DeepPavlov Dream Socialbot.
This is almost the same version of the DREAM socialbot as at
[the end of Alexa Prize Challenge 4](https://d7qzviu3xw2xc.cloudfront.net/alexa/alexaprize/docs/sgc4/MIPT-DREAM.pdf).
Some API services are replaced with trainable models.
Some services (e.g., News Annotator, Game Skill, Weather Skill) require private keys for underlying APIs,
most of them can be obtained for free.
If you want to use these services in local deployments, add your keys to the environmental variables (e.g., `./.env`, `./.env_ru`).
This version of Dream Socialbot consumes a lot of resources
because of its modular architecture and original goals (participation in Alexa Prize Challenge).
We provide a demo of Dream Socialbot on [our website](https://demo.deeppavlov.ai).

### Dream Mini

Mini version of DeepPavlov Dream Socialbot.
This is a generative-based socialbot that uses [English DialoGPT model](https://huggingface.co/microsoft/DialoGPT-medium) to generate most of the responses. It also contains intent catcher and responder components to cover special user requests.
[Link to the distribution.](https://github.com/deeppavlov/dream/tree/main/assistant_dists/dream_mini)

### Dream Russian

Russian version of DeepPavlov Dream Socialbot. This is a generative-based socialbot that uses [Russian DialoGPT by DeepPavlov](https://huggingface.co/DeepPavlov/rudialogpt3_medium_based_on_gpt2_v2) to generate most of the responses. It also contains intent catcher and responder components to cover special user requests. 
[Link to the distribution.](https://github.com/deeppavlov/dream/tree/main/assistant_dists/dream_russian)

### Prompted Dream Distributions

Mini version of DeepPavlov Dream Socialbot with the use of prompt-based generative models. 
This is a generative-based socialbot that uses large language models to generate most of the responses. 
You can upload your own prompts (json files) to [common/prompts](https://github.com/deeppavlov/dream/common/prompts),
add prompt names to `PROMPTS_TO_CONSIDER` (comma-separated),
and the provided information will be used in LLM-powered reply generation as a prompt.
[Link to the distribution.](https://github.com/deeppavlov/dream/tree/main/assistant_dists/dream_persona_prompted)

# Quick Start

### Clone the repo

```
git clone https://github.com/deeppavlov/dream.git
```

### Install [docker](https://docs.docker.com/engine/install/) and [docker-compose](https://docs.docker.com/compose/install/)

If you get a "Permission denied" error running docker-compose, make sure to [configure your docker user](https://docs.docker.com/engine/install/linux-postinstall/) correctly.

### Run one of the Dream distributions

#### **Deepy Base**

```
docker-compose -f docker-compose.yml -f assistant_dists/deepy_base/docker-compose.override.yml up --build
```

#### **Deepy Advanced**

```
docker-compose -f docker-compose.yml -f assistant_dists/deepy_adv/docker-compose.override.yml up --build
```

#### **Deepy FAQ**

```
docker-compose -f docker-compose.yml -f assistant_dists/deepy_faq/docker-compose.override.yml up --build
```

#### **Deepy GoBot**

```
docker-compose -f docker-compose.yml -f assistant_dists/deepy_gobot_base/docker-compose.override.yml up --build
```

#### **Dream (via proxy)**

The easiest way to try out Dream is to deploy it via proxy.
All the requests will be redirected to DeepPavlov API, so you don't have to use any local resources.
See [proxy usage](#proxy-usage) for details.

```
docker-compose -f docker-compose.yml -f assistant_dists/dream/docker-compose.override.yml -f assistant_dists/dream/dev.yml -f assistant_dists/dream/proxy.yml up --build
```

#### **Dream (locally)**

**Please note, that DeepPavlov Dream components require a lot of resources.**
Refer to the [components](#components) section to see estimated requirements.

```
docker-compose -f docker-compose.yml -f assistant_dists/dream/docker-compose.override.yml -f assistant_dists/dream/dev.yml up --build
```

We've also included a config with GPU allocations for multi-GPU environments:
```
AGENT_PORT=4242 docker-compose -f docker-compose.yml -f assistant_dists/dream/docker-compose.override.yml -f assistant_dists/dream/dev.yml -f assistant_dists/dream/test.yml up
```

When you need to restart particular docker container without re-building (make sure mapping in `assistant_dists/dream/dev.yml` is correct):

```
AGENT_PORT=4242 docker-compose -f docker-compose.yml -f assistant_dists/dream/docker-compose.override.yml -f assistant_dists/dream/dev.yml restart container-name
```

#### **Prompted Dream**

```
docker-compose -f docker-compose.yml -f assistant_dists/dream_persona_prompted/docker-compose.override.yml -f assistant_dists/dream_persona_prompted/dev.yml -f assistant_dists/dream_persona_prompted/proxy.yml up --build
```

We've also included a config with GPU allocations for multi-GPU environments.

### Let's chat

DeepPavlov Agent provides several options for interaction: a command line interface, an HTTP API, and a Telegram bot 

#### CLI

In a separate terminal tab run:

```
docker-compose exec agent python -m deeppavlov_agent.run agent.channel=cmd agent.pipeline_config=assistant_dists/dream/pipeline_conf.json
```

Enter your username and have a chat with Dream!

#### HTTP API

Once you've started the bot, DeepPavlov's Agent API will run on `http://localhost:4242`.
You can learn about the API from the [DeepPavlov Agent Docs](https://deeppavlov-agent.readthedocs.io/en/latest/intro/overview.html#http-api-server).

A basic chat interface will be available at `http://localhost:4242/chat`.

#### Telegram Bot
Currently, Telegram bot is deployed **instead** of HTTP API.
Edit `agent` `command` definition inside `docker-compose.override.yml` config:
```
agent:
  command: sh -c 'bin/wait && python -m deeppavlov_agent.run agent.channel=telegram agent.telegram_token=<TELEGRAM_BOT_TOKEN> agent.pipeline_config=assistant_dists/dream/pipeline_conf.json'
```
**NOTE:** treat your Telegram token as a secret and do not commit it to public repositories!

# Configuration and proxy usage

Dream uses several docker-compose configuration files:

`./docker-compose.yml` is the core config which includes containers for DeepPavlov Agent and mongo database;

`./assistant_dists/*/docker-compose.override.yml` lists all components for the distribution;

`./assistant_dists/dream/dev.yml` includes volume bindings for easier Dream debugging;

`./assistant_dists/dream/proxy.yml` is a list of proxied containers.

If your deployment resources are limited, you can replace containers with their proxied copies hosted by DeepPavlov.
To do this, override those container definitions inside `proxy.yml`, e.g.:

```
convers-evaluator-annotator:
  command: ["nginx", "-g", "daemon off;"]
  build:
    context: dp/proxy/
    dockerfile: Dockerfile
  environment:
    - PROXY_PASS=dream.deeppavlov.ai:8004
    - PORT=8004
```

and include this config in your deployment command:

```
docker-compose -f docker-compose.yml -f assistant_dists/dream/docker-compose.override.yml -f assistant_dists/dream/dev.yml -f assistant_dists/dream/proxy.yml up --build
```

By default, `proxy.yml` contains all available proxy definitions.

# Components English Version

Dream Architecture is presented in the following image:
![DREAM](DREAM.png)

| Name                | Requirements | Description                                                                                                                                                                    |
|---------------------|--------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Rule Based Selector |              | Algorithm that selects list of skills to generate candidate responses to the current context based on topics, entities, emotions, toxicity, dialogue acts and dialogue history |
| Response Selector   | 50 MB RAM    | Algorithm that selects a final responses among the given list of candidate responses                                                                                           |

## Annotators

| Name                        | Requirements           | Description                                                                                                                                                                                                                    |
|-----------------------------|------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| ASR                         | 40 MB RAM              | calculates overall ASR confidence for a given utterance and grades it as either _very low_, _low_, _medium_, or _high_ (for Amazon markup)                                                                                     |
| Badlisted Words             | 150 MB RAM             | detects words and phrases from the badlist                                                                                                                                                                                     |
| Combined Classification     | 1.5 GB RAM, 3.5 GB GPU | BERT-based model including topic classification, dialog acts classification, sentiment, toxicity, emotion, factoid classification                                                                                              |
| COMeT Atomic                | 2 GB RAM, 1.1 GB GPU   | Commonsense prediction models COMeT Atomic                                                                                                                                                                                     |
| COMeT ConceptNet            | 2 GB RAM, 1.1 GB GPU   | Commonsense prediction models COMeT  ConceptNet                                                                                                                                                                                |
| Convers Evaluator Annotator | 1 GB RAM, 4.5 GB GPU   | is trained on the Alexa Prize data from the previous competitions and predicts whether the candidate response is interesting, comprehensible, on-topic, engaging, or erroneous                                                 |
| Emotion Classification      | 2.5 GB RAM             | emotion classification annotator                                                                                                                                                                                               |
| Entity Detection            | 1.5 GB RAM, 3.2 GB GPU | extracts entities and their types from utterances                                                                                                                                                                              |
| Entity Linking              | 2.5 GB RAM, 1.3 GB GPU | finds Wikidata entity ids for the entities detected with Entity Detection                                                                                                                                                      |
| Entity Storer               | 220 MB RAM             | a rule-based component, which stores entities from the user's and socialbot's utterances if opinion expression is detected with patterns or MIDAS Classifier and saves them along with the detected attitude to dialogue state |
| Fact Random                 | 50 MB RAM              | returns random facts for the given entity (for entities from user utterance)                                                                                                                                                   |
| Fact Retrieval              | 7.4 GB RAM, 1.2 GB GPU | extracts facts from Wikipedia and wikiHow                                                                                                                                                                                      |
| Intent Catcher              | 1.7 GB RAM, 2.4 GB GPU | classifies user utterances into a number of predefined intents which are trained on a set of phrases and regexps                                                                                                               |
| KBQA                        | 2 GB RAM, 1.4 GB GPU   | answers user's factoid questions based on Wikidata KB                                                                                                                                                                          |
| MIDAS Classification        | 1.1 GB RAM, 4.5 GB GPU | BERT-based model trained on a semantic classes subset of MIDAS dataset                                                                                                                                                         |
| MIDAS Predictor             | 30 MB RAM              | BERT-based model trained on a semantic classes subset of MIDAS dataset                                                                                                                                                         |
| NER                         | 2.2 GB RAM, 5 GB GPU   | extracts person names, names of locations, organizations from uncased text                                                                                                                                                     |
| News API Annotator          | 80 MB RAM              | extracts the latest news about entities or topics using the GNews API. DeepPavlov Dream deployments utilize our own API key.                                                                                                   |
| Personality Catcher         | 30 MB RAM              |                                                                                                                                                                                                                                |
| Prompt Selector             | 50 MB RAM              | Annotator utilizing Sentence Ranker to rank prompts and selecting `N_SENTENCES_TO_RETURN` most relevant prompts (based on questions provided in prompts)                                                                       |
| Property Extraction         | 6.3 GiB RAM            | extracts user attributes from utterances                                                                                                                                                                                       |
| Rake Keywords               | 40 MB RAM              | extracts keywords from utterances with the help of RAKE algorithm                                                                                                                                                              |
| Relative Persona Extractor  | 50 MB RAM              | Annotator utilizing Sentence Ranker to rank persona sentences and selecting `N_SENTENCES_TO_RETURN` the most relevant sentences                                                                                                |
| Sentrewrite                 | 200 MB RAM             | rewrites user's utterances by replacing pronouns with specific names that provide more useful information to downstream components                                                                                             |
| Sentseg                     | 1 GB RAM               | allows us to handle long and complex user's utterances by splitting them into sentences and recovering punctuation                                                                                                             |
| Spacy Nounphrases           | 180 MB RAM             | extracts nounphrases using Spacy and filters out generic ones                                                                                                                                                                  |
| Speech Function Classifier  | 1.1 GB RAM, 4.5 GB GPU | a hierarchical algorithm based on several linear models and a rule-based approach for the prediction of speech functions described by Eggins and Slade                                                                         |
| Speech Function Predictor   | 1.1 GB RAM, 4.5 GB GPU | yields probabilities of speech functions that can follow a speech function predicted by Speech Function Classifier                                                                                                             |
| Spelling Preprocessing      | 50 MB RAM              | pattern-based component to rewrite different colloquial expressions to a more formal style of conversation                                                                                                                     |
| Topic Recommendation        | 40 MB RAM              | offers a topic for further conversation using the information about the discussed topics and user's preferences. Current version is based on Reddit personalities (see Dream Report for Alexa Prize 4).                        |
| Toxic Classification        | 3.5 GB RAM, 3 GB GPU   | Toxic classification model from Transformers specified as PRETRAINED_MODEL_NAME_OR_PATH                                                                                                                                        |
| User Persona Extractor      | 40 MB RAM              | determines which age category the user belongs to based on some key words                                                                                                                                                      |
| Wiki Parser                 | 100 MB RAM             | extracts Wikidata triplets for the entities detected with Entity Linking                                                                                                                                                       |
| Wiki Facts                  | 1.7 GB RAM             | model that extracts related facts from Wikipedia and WikiHow pages                                                                                                                                                             |

## Services
| Name                   | Requirements            | Description                                                                                                                                                                                                                                |
|------------------------|-------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| DialoGPT               | 1.2 GB RAM, 2.1 GB GPU  | generative service based on Transformers generative model, the model is set in docker compose argument `PRETRAINED_MODEL_NAME_OR_PATH` (for example, `microsoft/DialoGPT-small` with 0.2-0.5 sec on GPU)                                   |
| DialoGPT Persona-based | 1.2 GB RAM, 2.1 GB GPU  | generative service based on Transformers generative model, the model was pre-trained on the PersonaChat dataset to generate a response conditioned on a several sentences of the socialbot's persona                                       |
| Image Captioning       | 4 GB RAM, 5.4 GB GPU    | creates text representation of a received image                                                                                                                                                                                            |
| Infilling              | 1  GB RAM, 1.2 GB GPU   | (turned off but the code is available) generative service based on Infilling model, for the given utterance returns utterance where `_` from original text is replaced with generated tokens                                               |
| Knowledge Grounding    | 2 GB RAM, 2.1 GB GPU    | generative service based on BlenderBot architecture providing a response to the context taking into account an additional text paragraph                                                                                                   |
| Masked LM              | 1.1 GB RAM, 1 GB GPU    | (turned off but the code is available)                                                                                                                                                                                                     |
| Seq2seq Persona-based  | 1.5 GB RAM, 1.5 GB GPU  | generative service based on Transformers seq2seq model, the model was pre-trained on the PersonaChat dataset to generate a response conditioned on a several sentences of the socialbot's persona                                          |
| Sentence Ranker        | 1.2 GB RAM, 2.1 GB GPU  | ranking model given as `PRETRAINED_MODEL_NAME_OR_PATH` which for a pair os sentences returns a float score of correspondence                                                                                                               |
| StoryGPT               | 2.6 GB RAM, 2.15 GB GPU | generative service based on fine-tuned GPT-2, for the given set of keywords returns a short story using the keywords                                                                                                                       |
| GPT-3.5                | 100 MB RAM              | generative service based on OpenAI API service, the model is set in docker compose argument `PRETRAINED_MODEL_NAME_OR_PATH` (in particular, in this service, `text-davinci-003` is used.                                                   |
| ChatGPT                | 100 MB RAM              | generative service based on OpenAI API service, the model is set in docker compose argument `PRETRAINED_MODEL_NAME_OR_PATH` (in particular, in this service, `gpt-3.5-turbo` is used.                                                      |
| Prompt StoryGPT        | 3 GB RAM, 4 GB GPU      | generative service based on fine-tuned GPT-2, for the given topic represented by one noun returns short story on a given topic                                                                                                             |
| GPT-J 6B               | 1.5 GB RAM, 24.2 GB GPU | generative service based on Transformers generative model, the model is set in docker compose argument `PRETRAINED_MODEL_NAME_OR_PATH` (in particular, in this service, [GPT-J model](https://huggingface.co/EleutherAI/gpt-j-6B) is used. |

## Skills
| Name                               | Requirements              | Description                                                                                                                                                                                                                                                   |
|------------------------------------|---------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Alexa Handler                      | 30 MB RAM                 | handler for several specific Alexa commands                                                                                                                                                                                                                   |
| Christmas Skill                    | 30 MB RAM                 | supports FAQ, facts, and scripts for Christmas                                                                                                                                                                                                                |
| Comet Dialog skill                 | 300 MB RAM                | uses COMeT ConceptNet model to express an opinion, to ask a question or give a comment about user's actions mentioned in the dialogue                                                                                                                         |
| Convert Reddit                     | 1.2 GB RAM                | uses a ConveRT encoder to build efficient representations for sentences                                                                                                                                                                                       |
| Dummy Skill                        | a part of agent container | a fallback skill with multiple non-toxic candidate responses                                                                                                                                                                                                  |
| Dummy Skill Dialog                 | 600 MB RAM                | returns the next turn from the Topical Chat dataset if the response of the user to the Dummy Skill is similar to the corresponding response in the source data                                                                                                |
| Eliza                              | 30 MB RAM                 | Chatbot (https://github.com/wadetb/eliza)                                                                                                                                                                                                                     |
| Emotion Skill                      | 40 MB RAM                 | returns template responses to emotions detected by Emotion Classification from Combined Classification annotator                                                                                                                                              |
| Factoid QA                         | 170 MB RAM                | answers factoid questions                                                                                                                                                                                                                                     |
| Game Cooperative Skill             | 100 MB RAM                | provides user with a conversation about computer games: the charts of the best games for the past year, past month, and last week                                                                                                                             |
| Harvesters Maintenance Skill       | 30 MB RAM                 | Harvesters maintenance skill                                                                                                                                                                                                                                  |
| Harvesters Maintenance Gobot Skill | 30 MB RAM                 | Harvesters maintenance Goal-oriented skill                                                                                                                                                                                                                    |
| Knowledge Grounding Skill          | 100 MB RAM                | generates a response based on the dialogue history and provided knowledge related to the current conversation topic                                                                                                                                           |
| Meta Script Skill                  | 150 MB RAM                | provides a multi-turn dialogue around human activities. The skill uses COMeT Atomic model to generate commonsensical descriptions and questions on several aspects                                                                                            |
| Misheard ASR                       | 40 MB RAM                 | uses the ASR Processor annotations to give feedback to the user when ASR confidence is too low                                                                                                                                                                |
| News API Skill                     | 60 MB RAM                 | presents the top-rated latest news about entities or topics using the GNews API                                                                                                                                                                               |
| Oscar Skill                        | 30 MB RAM                 | supports FAQ, facts, and scripts for Oscar                                                                                                                                                                                                                    |
| Personal Info Skill                | 40 MB RAM                 | queries and stores user's name, birthplace, and location                                                                                                                                                                                                      |
| DFF Program Y Skill                | 800 MB RAM                | **[New DFF version]** Chatbot Program Y (https://github.com/keiffster/program-y) adapted for Dream socialbot                                                                                                                                                  |
| DFF Program Y Dangerous Skill      | 100 MB RAM                | **[New DFF version]** Chatbot Program Y (https://github.com/keiffster/program-y) adapted for Dream socialbot, containing responses to dangerous situations in a dialog                                                                                        |
| DFF Program Y Wide Skill           | 110 MB RAM                | **[New DFF version]** Chatbot Program Y (https://github.com/keiffster/program-y) adapted for Dream socialbot, which includes only very general templates (with lower confidence)                                                                              |
| Small Talk Skill                   | 35 MB RAM                 | asks questions using the hand-written scripts for 25 topics, including but not limited to love, sports, work, pets, etc.                                                                                                                                      |
| SuperBowl Skill                    | 30 MB RAM                 | supports FAQ, facts, and scripts for SuperBowl                                                                                                                                                                                                                |
| Text QA                            | 1.8 GB RAM, 2.8 GB GPU    |                                                                                                                                                                                                                                                               |
| Valentine's Day Skill              | 30 MB RAM                 | supports FAQ, facts, and scripts for Valentine's Day                                                                                                                                                                                                          |
| Wikidata Dial Skill                | 100 MB RAM                | generates an utterance using Wikidata triplets. Not turned on, needs improvement                                                                                                                                                                              |
| DFF Animals Skill                  | 200 MB RAM                | is created using DFF and has three branches of conversation about animals: user's pets, pets of the socialbot, and wild animals                                                                                                                               |
| DFF Art Skill                      | 100 MB RAM                | DFF-based skill to discuss art                                                                                                                                                                                                                                |
| DFF Book Skill                     | 400 MB RAM                | **[New DFF version]** detects book titles and authors mentioned in the user's utterance with the help of Wiki parser and Entity linking and recommends books by leveraging information from the GoodReads database                                            |
| DFF Bot Persona Skill              | 150 MB RAM                | aims to discuss user favorites and 20 most popular things with short stories expressing the socialbot's opinion towards them                                                                                                                                  |
| DFF Coronavirus Skill              | 110 MB RAM                | **[New DFF version]** retrieves data about the number of coronavirus cases and deaths in different locations sourced from the John Hopkins University Center for System Science and Engineering                                                               |
| DFF Food Skill                     | 150 MB RAM                | constructed with DFF to encourage food-related conversation                                                                                                                                                                                                   |
| DFF Friendship Skill               | 100 MB RAM                | **[New DFF version]** DFF-based skill to greet the user in the beginning of the dialog, and forward the user to some scripted skill                                                                                                                           |
| DFF Funfact Skill                  | 100 MB RAM                | **[New DFF version]** Tells user fun facts                                                                                                                                                                                                                    |
| DFF Gaming Skill                   | 80 MB RAM                 | provides a video games discussion. Gaming Skill is for more general talk about video games                                                                                                                                                                    |
| DFF Gossip Skill                   | 95 MB RAM                 | DFF-based skill to discuss other people with news about them                                                                                                                                                                                                  |
| DFF Image Skill                    | 100 MB RAM                | **[New DFF version]** Scripted skill that based on the sent image captioning (from annotations) responses with specified responses in case of food, animals or people detected, and default responses otherwise                                               |
| DFF Template Skill                 | 50 MB RAM                 | **[New DFF version]** DFF-based skill that provides an example of DFF usage                                                                                                                                                                                   |
| DFF Template Prompted Skill        | 50 MB RAM                 | **[New DFF version]** DFF-based skill that provides answers generated by language model based on specified prompts and the dialog context. The model to be used is specified in GENERATIVE_SERVICE_URL. For example, you may use Transformer LM GPTJ service. |
| DFF Grounding Skill                | 90 MB RAM                 | **[New DFF version]** DFF-based skill to answer what is the topic of the conversation, to generate acknowledgement, to generate universal responses on some dialog acts by MIDAS                                                                              |
| DFF Intent Responder               | 100 MB RAM                | **[New DFF version]**  provides template-based replies for some of the intents detected by Intent Catcher annotator                                                                                                                                           |
| DFF Movie Skill                    | 1.1 GB RAM                | is implemented using DFF and takes care of the conversations related to movies                                                                                                                                                                                |
| DFF Music Skill                    | 70 MB RAM                 | DFF-based skill to discuss music                                                                                                                                                                                                                              |
| DFF Science Skill                  | 90 MB RAM                 | DFF-based skill to discuss science                                                                                                                                                                                                                            |
| DFF Short Story Skill              | 90 MB RAM                 | **[New DFF version]** tells user short stories from 3 categories: (1) bedtime stories, such as fables and moral stories, (2) horror stories, and (3) funny ones                                                                                               |
| DFF Sport Skill                    | 70 MB RAM                 | DFF-based skill to discuss sports                                                                                                                                                                                                                             |
| DFF Travel Skill                   | 70 MB RAM                 | DFF-based skill to discuss travel                                                                                                                                                                                                                             |
| DFF Weather Skill                  | 1.4 GB RAM                | **[New DFF version]** uses the OpenWeatherMap service to get the forecast for the user's location                                                                                                                                                             |
| DFF Wiki Skill                     | 150 MB RAM                | used for making scenarios with the extraction of entities, slot filling, facts insertion, and acknowledgements                                                                                                                                                |

## Prompted Skills
| Name                       | Requirements              | Description                                                                                                                                                                                                  |
|----------------------------|---------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| AI FAQ Skill               | 150 MB RAM                | **[New DFF version]** Everything you wanted to know about modern AI but was afraid to ask! This FAQ Assistant chats with you while explaining the simplest topics from today's technology world.             |
| da Costa Clothes Skill     | 150 MB RAM                | **[New DFF version]** Stay protected in every season with da Costa Industries Clothes Assistant! Experience the ultimate comfort and protection, no matter the weather. Stay warm in winter a...             |
| Dream Persona Skill        | 150 MB RAM                | **[New DFF version]** Prompt-based skill that utilizes given generative service to generate responses based on the given prompt                                                                              |
| Empathetic Marketing Skill | 150 MB RAM                | **[New DFF version]** Connect with your audience like never before with Empathetic Marketing AI Assistant! Reach new heights of success by tapping into the power of empathy. Say goodbye..                  |
| Fairytale Skill            | 150 MB RAM                | **[New DFF version]** This assistant will tell you or your children a short but engaging fairytale. Choose the characters and the topic and leave the rest to AI imagination.                                |
| Nutrition Skill            | 150 MB RAM                | **[New DFF version]** Discover the secret to healthy eating with our AI assistant! Find nutritious food options for you and your loved ones with ease. Say goodbye to mealtime stress and hello to delici... |
| Rhodes Coaching Skill      | 150 MB RAM                | **[New DFF version]** Unlock your full potential with Rhodes & Co's patented AI assistant! Reach peak performance at work and at home. Get into top form effortlessly and inspire others with.               |


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
