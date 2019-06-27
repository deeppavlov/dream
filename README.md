# DeepPavlov Agent

**DeepPavlov Agent** is a platform for creating multi-skill chatbots.

<p align="center">
    <img src="images/Agent%20Pipeline.png" height="600">
</p>

Ready Agent from the box
========================

To demonstrate the abilities of the platform, we included in this repo some basic skills and selectors
made on [DeepPavlov](https://github.com/deepmipt/DeepPavlov). Currently all these services are made only for **Russian language**.
Here are the types of conversation you will get if you run the Agent from the pre-made configuration:

<p align="center">
  <img src="images/conversation_1.jpg" width="200" />
  <img src="images/conversation_2.jpg" width="200" />
  <img src="images/conversation_3.jpg" width="200" />
</p>

Services Configuration
======================

You can configure services at the Agent [config file](../core/config.py).

**Config Description**

* **name**
    * An arbitrary and unique name of the service
* **protocol**
    * A web protocol, _**"http"**_ by default
* **host**
    * A service host machine name, _**"127.0.0.1"**_ by default
* **port**
    * A port on a service host machine
* **endpoint**
    * A service URL endpoint, _**"/skill"**_ by default
* **path**
    * A path to the agent service config file, currently valid only for DeepPavlov skills
* **env**
    * Environment variables dictionary
* **gpu**
    * If a service needs to be run on GPU, _**False**_ by default
* **external**
    * If the service is running from the **dp-agent** repo. _**False**_ by default.

Notice that if you want to run an Agent from only one skill, you can leave
**SKILL_SELECTORS** and **RESPONSE_SELECTORS** empty.

Also you can include in the Agent configuration any external service running on some other machine.

Services Deployment
===================
1. Create a new **Python 3.6.7** virtual environment.
1. Install requirements for Docker config generator:
    ```bash
    pip -r install gen_requirements.txt
    ```
1. Install and configure [Docker](https://docs.docker.com/install/) and [Docker-compose](https://docs.docker.com/compose/install/) (version 1.19.0 or later).

1. (optional) Install [nvidia-docker](https://github.com/NVIDIA/nvidia-docker) if you wish to run some services on GPU.

1. Create a directory for storing downloaded data, such as pre-trained models.
   It should be located outside the agent project's home directory.
   
1. Setup an `EXTERNAL_FOLDER` variable with the path to data directory. This path
    will be used by Agent to download models' data:
   
   ```dotenv
   EXTERNAL_FOLDER=<path to data directory>
   ```
1. (optional) If you want to communicate with the bot via Telegram, setup the following environment variables:

   ```dotenv
   TELEGRAM_TOKEN=<token>
   TELEGRAM_PROXY=socks5://<user>:<password>@<path:port>
   ```
   
   Here's an example of values:
   
   ```dotenv
   TELEGRAM_TOKEN=123456789:AAGCiO0QFb_I-GXL-CbJDw7--JQbHkiQyYA
   TELEGRAM_PROXY=socks5://tgproxy:tgproxy_pwd@123.45.67.89:1447
   ```
1. Configure all skills, skill selectors, response selectors, annotators and database connection in [core/config.py](core/config.py).
   If you want a particular skill to use GPU, set its `gpu` value to `True`.

   If you want a minimal configuration, you need one skill and one skill selector.
   Pick skill `chitchat` and  selector `chitchat_odqa` and comment out all other skills, selectors and annotators.
   
1. Generate a Docker environment configuration (`docker-compose.yml`) by running the command:

    ```bash
    python generate_composefile.py
    ```
    This configuration represents the choice of skills from the previous step.
    Re-generate it every time you change [core/config.py](core/config.py).
    
1. Run the Docker environment with:

     ```bash
     docker-compose up --build
     ```
   Now you have a working environment with the following services:
   
   * DeepPavlov Agent (`agent`)
   * MongoDB (`mongo`)
   * A service for each skill, selector or other component.
   
   In this shell you will now see the logs from all working services.

Running the Agent
=================

Agent can run both from container and from a local machine.

**Container**

1. Connect to agent's container:

    ```bash
    docker exec -it agent /bin/bash
    ```

    ([more information on `docker exec`](https://docs.docker.com/engine/reference/commandline/exec/))

1. Start communicating with the chatbot from the agent's container console:

    ```bash
    python3 -m core.run
    ```

**Local machine**

1. (optional) Please consider setting your locale according your input language to avoid decoding errors while communicating agent via command line.
   For example:

    ```bash
    export LANG="C.UTF-8"
    export LC_ALL="C.UTF-8"
    ```


1. Setup `DPA_LAUNCHING_ENV` environment variable:

    ```bash
    export DPA_LAUNCHING_ENV="local"
    ```

1. Install Agent requirements:
    ```bash
    pip -r install gen_requirements.txt
    ```

2. Start communicating with the chatbot from the console:
    ```bash
    python3 -m core.run
    ```
    or via the Telegram:

    ```bash
    python3 -m core.run -ch telegram
    ```
