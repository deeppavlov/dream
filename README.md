# DeepPavlov Agent

**DeepPavlov Agent** is a platform for creating multi-skill chatbots.

![arch](https://github.com/deepmipt/dp-agent/blob/dev/Agent%20Pipeline.png)


Deployment
==========
1. Create a new **Python 3.6.7** environment.
2. Install project docker config generator requirements:
    ```bash
    pip -r install gen_requirements.txt
    ```
3. Install and configure [Docker](https://docs.docker.com/install/) and [Docker-compose](https://docs.docker.com/compose/install/)
4. Set up an environmental variable for storing high volume downloadable data, like pre-trained models in [.env](../.env) file.
``EXTERNAL_FOLDER=''`` - this variable stores path for external folder where downloaded data will be stored. By default it is linked to project's homefolder.
5. Configure `TELEGRAM_TOKEN` and `TELEGRAM_PROXY` environment variables if you want to communicate with the bot via Telegram.
6. Configure all skills, skill selectors, response selectors, annotators and database connection in [config.py](core/config.py)
7. Generate **docker-compose.yml** by running the command:
    ```bash
    python generate_composefile.py

    ```
8. Run containers:
     ```bash
     docker-compose up --build
     ```

9. Connect to agent container ([more information](https://docs.docker.com/engine/reference/commandline/exec/)):
    ```bash
    docker exec -it agent /bin/bash
    ```

10. Start communicating with the chatbot from the agent container console:
    ```bash
    python3 -m core.run
    ```
    or via the Telegram:
    
    ```bash
    python3 -m core.run -ch telegram
    ```