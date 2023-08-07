# DFF Reasoning Skill

## Description

This skill utilizes OpenAI ChatGPT to think of actions required to handle user requests and to choose the relevant API.

### Parameters

```
API_CONFIGS: configuration files of APIs to consider splitted by comma, files stored in `dream/skills/dff_reasoning_skill/api_configs`
GENERATIVE_SERVICE_URL: LLM to utilize
GENERATIVE_SERVICE_CONFIG: configuration file with generative parameters to utilize
GENERATIVE_TIMEOUT: timeout for request to LLM
N_UTTERANCES_CONTEXT: number of last utterances to consider as a dialog context
ENVVARS_TO_SEND: API keys splitted by comma to get as env variables
TIME_SLEEP: time to sleep between LLM requests
```

## Dependencies

- LLM `GENERATIVE_SERVICE_URL`
- available APIs to consider
- API keys in environmental variables for key-required LLMs (OpenAI API, Anthropic API)


## How to get API keys

### OPENAI_API_KEY

Go to OpenAI and find your Secret API key in your [user settings](https://platform.openai.com/account/api-keys).


### GOOGLE_CSE_ID and GOOGLE_API_KEY

1. Create a new project [here](https://console.developers.google.com/apis/dashboard);

2. Create a new API key [here](https://console.developers.google.com/apis/credentials);

3. Enable the Custom Search API [here](https://console.developers.google.com/apis/library/customsearch.googleapis.com);

4. Create a new Custom Search Engine [here](https://cse.google.com/cse/all);

5. Add your API Key and your Custom Search Engine ID to your .env_secret file.

### OPENWEATHERMAP_API_KEY
 
Sign up [here](https://openweathermap.org) and the API key (APPID) will be sent to you in a confirmation email.

### NEWS_API_KEY

Go [here](https://newsapi.org) and click on Get API Key button.

### WOLFRAMALPHA_APP_ID

Sign up [here](https://account.wolfram.com/auth/create), go to the My Apps tab, and create an app to get APPID.

