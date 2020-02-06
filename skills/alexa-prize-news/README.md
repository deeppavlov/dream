# AlexaPrize


## Install dependencies
Install dependencies:
`pip install requirements.txt`
Also install zdialog and pytest if you run without docker


## Run
`python run.py`
Command line arguments:

     `--host`:  Host on which to run API (default - HOST env variable or "0.0.0.0")
     `--port`:  Port on which to run API (default - PORT env variable or 3672)


     `--dev_tg_token`:   Telegram Token for Dev version. If None, run production version (default - DEV_TG_TOKEN env variable)


It is recommended to use env variables instead of CLI arguments

Run tests:
`pytest tests`

## Docker

Run production version: 

`docker volume create prod_contexts`

`docker build -t alexaprize_prod .`

```
docker run 
--name alexaprize_prod 
-p3672:3672
--mount source=prod_contexts,target=/tmp/contexts
-v "$(pwd)"/data:/data
-v "$(pwd)"/news_models_files:/news_models_files
alexaprize_prod
```

Run dev version: 

`docker build -f dev.Dockerfile -t alexaprize_dev .`

`docker run --name alexaprize_dev --net=host -d alexaprize_dev`
    
Run tests: 

`docker build -f tests.Dockerfile -t alexaprize_tests .`

`docker run --name alexaprize_tests alexaprize_tests`
    




