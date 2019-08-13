Architecture Overview
=====================

**DeepPavlov Agent** helps production chatbot developers to organize multiple NLP models in a single pipeline.
Modern chatbots usually solve different tasks (like chitchat, goal-oriented, question answering) simultaneously,
so the platform should have the following characteristics:

    * be stable at highload environment
    * save and pass the chatbot state_ across all the connected models

.. image:: ../_static/Agent_Pipeline.png
   :height: 600
   :align: center
   :alt: Architecture

**Key concepts in DeepPavlov Agent architecture:**

* ``Utterance`` is a single message produced by a human or a bot;

* ``Service`` is any NLP model that can be inferred as a REST service.

  There are different types of services:

    * ``Annotator`` is a service for utterance preprocessing. It can be some basic text preprocessing like
      coreference resolution, named entiry recognition, spell correction, etc.;

    * ``Skill`` is a service producing a bot reply to a user utterance;

    * ``Skill Selector`` is a service choosing which bunch of available skills should be responsible
      for producing possible bot replies;

    * ``Response Selector`` is a service choosing a single bot reply from the available replies;

    * ``Postprocessor`` is a service postprocessing a bot utterance. It can make some basic things
      like adding a user name to the reply, inserting emojis, etc.;

    * ``Response`` is a final postprocessed bot utterance that is shown to the user.

    * ``State`` is current dialogs between users and a bot serialized as **json**. State is used to pass information
      across the services and contains all possibly needed information about the current dialogs.
      It has separate `documentation <state_>`__.


Ready Agent from the box
========================

To demonstrate the abilities of the platform, we included in this repo some basic skills and selectors
made on DeepPavlov_. Currently all these services are made only for **Russian language**.
Here are the types of conversation you will get if you run the Agent from the pre-made configuration:

|pic1|  |pic2|  |pic3|

.. |pic1| image:: ../_static/conversation_1.jpg
   :width: 30%

.. |pic2| image:: ../_static/conversation_2.jpg
   :width: 30%

.. |pic3| image:: ../_static/conversation_3.jpg
   :width: 30%

Services Configuration
======================

You can configure services at the Agent `config file`_.

**Config Description**

* **name**
    * An arbitrary and unique name of the service
* **protocol**
    * A web protocol, **"http"** by default
* **host**
    * A service host machine name, **"127.0.0.1"** by default
* **port**
    * A port on a service host machine
* **endpoint**
    * A service URL endpoint, **"/skill"** by default
* **path**
    * A path to the agent service config file, currently valid only for DeepPavlov skills
* **env**
    * Environment variables dictionary
* **gpu**
    * If a service needs to be run on GPU, **False** by default
* **external**
    * If the service is running from the **dp-agent** repo. **False** by default.
* **formatter**
    * The name of a function that converts the Agent state into a service input format
      and converts a service output format into the Agent state

Notice that if you want to run an Agent from only one skill, you can leave
**SKILL_SELECTORS** and **RESPONSE_SELECTORS** empty.

Also you can include in the Agent configuration any external service running on some other machine.

Services Deployment
===================
1. Create a new **Python 3.6.7** virtual environment.

2. Install requirements for Docker config generator:

    .. code:: bash

        pip -r install gen_requirements.txt

3. Install and configure Docker_ and Docker-compose_ (version 1.19.0 or later).

4. (optional) Install nvidia-docker_ if you wish to run some services on GPU.

5. Create a directory for storing downloaded data, such as pre-trained models.
   It should be located outside the agent project's home directory.

6. Setup an **EXTERNAL_FOLDER** variable with the path to data directory. This pat will be used by Agent to download models' data:

    .. code:: bash

        EXTERNAL_FOLDER=<path to data directory>

7. (optional) If you want to communicate with the bot via Telegram, setup the following environment variables:

   .. code:: bash

       TELEGRAM_TOKEN=<token>
       TELEGRAM_PROXY=socks5://<user>:<password>@<path:port>

   Here's an example of values:

   .. code:: bash

       TELEGRAM_TOKEN=123456789:AAGCiO0QFb_I-GXL-CbJDw7--JQbHkiQyYA
       TELEGRAM_PROXY=socks5://tgproxy:tgproxy_pwd@123.45.67.89:1447

8. Configure all skills, skill selectors, response selectors, annotators and database connection in the `config file`_.
   If you want a particular skill to use GPU, set its ``gpu`` value to ``True``.

   If you want a minimal configuration, you need one skill and one skill selector.
   Pick skill ``chitchat`` and  selector ``chitchat_odqa`` and comment out all other skills, selectors and annotators.

9. Generate a `Docker environment configuration`_  by running the command:

    .. code:: bash

        python generate_composefile.py

    This configuration represents the choice of skills from the previous step.
    Re-generate it every time you change `config file`_.

10. Run the Docker environment with:

     .. code:: bash

         docker-compose up --build

   Now you have a working environment with the following services:

   * DeepPavlov Agent (``agent``)
   * MongoDB (``mongo``)
   * A service for each skill, selector or other component.

   In this shell you will now see the logs from all working services.

Running the Agent
=================

Agent can run both from container and from a local machine.

**Container**

1. Connect to agent's container:

    .. code:: bash

        docker exec -it agent /bin/bash

    (more information on docker-exec_)

2. Start communicating with the chatbot from the agent's container console:

    .. code:: bash

        python3 -m core.run

**Local machine**

1. (optional) Please consider setting your locale according your input language to avoid decoding errors while communicating agent via command line.
   For example:

    .. code:: bash

        export LANG="C.UTF-8"
        export LC_ALL="C.UTF-8"


2. Setup **DPA_LAUNCHING_ENV** environment variable:

    .. code:: bash

        export DPA_LAUNCHING_ENV="local"

3. Install Agent requirements:

    .. code:: bash

        pip -r install gen_requirements.txt

4. Start communicating with the chatbot from the console:

    .. code:: bash

        python3 -m core.run

    or via the Telegram:

    .. code:: bash

        python3 -m core.run -ch telegram

**HTTP api server**

1. You can run agent api server from both container and local environment:

    .. code:: bash

        python3 -m core.run -ch http_client [-p 8888]

    In both cases api will be accessible on your localhost

2. Web server accepts POST requests with application/json content-type:

    Request should be in form:

    .. code:: javascript

        {
          "user_id": "unique id of user",
          "payload": "phrase, which should be processed by agent"
        }

    Example of running request with curl:

    .. code:: bash

        curl --header "Content-Type: application/json" \
             --request POST \
             --data '{"user_id":"xyz","payload":"hello"}' \
             http://localhost:8888

    Agent will return a json response:

    .. code:: javascript

        {
          "user_id": "same user id as in request",
          "response": "phrase, which were generated by skills in order to respond"
        }

    In case of wrong format, HTTP errors will be returned

.. _config file: https://github.com/deepmipt/dp-agent/blob/master/core/config.py
.. _DeepPavlov: https://github.com/deepmipt/DeepPavlov
.. _Docker: https://docs.docker.com/install/
.. _Docker-compose: https://docs.docker.com/compose/install/
.. _nvidia-docker: https://github.com/NVIDIA/nvidia-docker
.. _Docker environment configuration: https://github.com/deepmipt/dp-agent/blob/master/docker-compose.yml
.. _docker-exec: https://docs.docker.com/engine/reference/commandline/exec/
.. _state: https://deeppavlov-agent.readthedocs.io/en/latest/_static/api.html