Deployment
==========
1. Install project requirements.
2. Configure and run `Mongo DB` in [connection.py](connection.py)
3. Configure and run skills, skill selectors, response selectors and annotators servers in [config.py](config.py).

    * don't change ``name`` fields
    * all configs where ``path`` is not ``None`` are DeepPavlov's configs and they can run in `skill` riseapi mode: 
    ```bash
    python -m deeppavlov riseapi --api-mode skill <CONFIG_REL_PATH> --port <PORT> --endpoint <ENDPOINT>
    ```
    * ``hellobot`` skill is not DeepPavlov's, it has a separate [instruction]( https://github.com/acriptis/dj_bot/blob/master/hello_bot/README.md#deployment) how to deploy it.
    * ``odqa`` skill should run on GPU. For other DeepPavlov skills GPU is not critical.
4. Configure `TELEGRAM_TOKEN` and `TELEGRAM_PROXY` environment variables.
5. Run [run.py](run.py). Conversation with the Agent should become available via Telegram.

Docker
======
1. Install and configure [Docker](https://docs.docker.com/install/) and [Docker-compose](https://docs.docker.com/compose/install/)
2. Set up an environmental variable for storing high volume downloadable data, like pre-trained models in [.env](../.env) file.
``EXTERNAL_FOLDER=''`` - this variable stores path for external folder where downloaded data will be stored. By default it is linked to project's homefolder.
3. Configure all skills, skill selectors, response selectors and annotators in [config.py](config.py)
4. Set up all containers in [docker-compose.yml](../docker-compose.yml) file. Below you can find a skill configuration from config.py file and relevant part from docker-compose.yml:

    ```json
    {
        "name": "chitchat",
        "url": "http://chitchat:2081/chitchat",
        "path": root / "skills/ranking_chitchat/agent_ranking_chitchat_2staged_tfidf_smn_v4_prep.json",
        "env": {
            "CUDA_VISIBLE_DEVICES": ""
        },
        "profile_handler": True
    }
    ```

    ```yaml  
    chitchat:
        build:
          context: ./
          dockerfile: dockerfile_skill_basic
          args:
            skillconfig: skills/ranking_chitchat/agent_ranking_chitchat_2staged_tfidf_smn_v4_prep.json
            skillport: 2081
        container_name: chitchat
        volumes:
         - .:/dp-agent
         - ${EXTERNAL_FOLDER}dp_logs:/logs
         - ${EXTERNAL_FOLDER}.deeppavlov:/root/.deeppavlov
        ports:
         - "2081:2081"
        tty: true
    ```

    * **url** from [config.py](config.py) should contain **container_name** and **skillport** from [docker-compose.yml](../docker-compose.yml)
    * **path** (without root variable) from [config.py](config.py) should be equal to **skillconfig** from [docker-compose.yml](../docker-compose.yml)
6. Configure database connection in [connection.py](connection.py) (by default, container is configured for mongoDB)
5. Run using ```docker-compose up --build``` command
6. Connect to agent container using ```docker exec -it agent /bin/bash``` https://docs.docker.com/engine/reference/commandline/exec/