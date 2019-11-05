Architecture Overview
=====================

**DeepPavlov Agent** helps production chatbot developers to organize multiple NLP models in a single pipeline.
Modern chatbots usually solve different tasks (like chitchat, goal-oriented, question answering) simultaneously,
so the platform should have the following characteristics:

    * be stable at highload environment
    * save and pass the chatbot state_ across all the connected models

.. image:: ../_static/Agent_Pipeline_v2.png
   :height: 600
   :align: center
   :alt: Architecture

**Key concepts in DeepPavlov Agent architecture:**

* ``Utterance`` is a single message produced by a human or a bot;

* ``Service`` is any NLP model that can be inferred as a REST service.

  There are different types of services:

    * ``Annotator`` is a service for utterance preprocessing. It can be some basic text preprocessing like
      coreference resolution, named entity recognition, spell correction, etc.;

    * ``Skill`` is a service producing a bot reply to a user utterance;

    * ``Skill Selector`` is a service choosing which bunch of available skills should be responsible
      for producing possible bot replies;

    * ``Response Selector`` is a service choosing a single bot reply from the available replies;

    * ``Postprocessor`` is a service postprocessing a bot utterance. It can make some basic things
      like adding a user name to the reply, inserting emojis, etc.;

* ``Postprocessed Response`` is a final postprocessed bot utterance that is shown to the user.

* ``State`` is current dialogs between users and a bot serialized as **json**. State is used to pass information
  across the services and contains all possibly needed information about the current dialogs.
  It has separate `documentation <state_>`__.


Ready Agent from the box
========================

To demonstrate the abilities of the platform, we included in this repo some basic skills and selectors
made on DeepPavlov_. Currently all these services are made only for **Russian language**.

Services Configuration
======================

You can configure services at the Agent `config file`_.

**Config Description**

**Database**

All default values are taken from `Mongo DB documentation <mongo-docs_>`__. Please refer to these docs if you need to
change anything.

* **DB_NAME**
    * An name of the database. Default name is **"test"**
* **DB_HOST**
    * A database host, **"127.0.0.1"** by default
* **DB_PORT**
    * A database port, **"27017"** by default
* **DB_PATH**
    * A database data path. Default path is **"/data/db"**.

    Please make sure that this path exists on your machine and has valid permissions.


**Services**

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
* **url** (optional)
    * A service url. By default it is generated from **protocol + host + port +  endpoint**
* **path**
    * A path to the agent service config file, currently valid only for DeepPavlov skills
* **env**
    * Environment variables dictionary
* **external** (optional)
    * If the service is running from the **dp-agent** repo. **False** by default.
* **dockerfile** (optional)
    * Specify a dockerfile name available inside the Agent repo. **"dockerfile_skill_cpu"** by default.

    Available options:

        * **"dockerfile_skill_cpu"**
        * **"dockerfile_skill_gpu"**
* **formatter**
    * The name of a function that converts the Agent state into a service input format
      and converts a service output format into the Agent state
* **batch_size** (optional)
    A size of input batch for the services. By default it's always 1, but for neural services it is usually makes more
    sense to increase it for better performance.


Notice that you can leave **SKILL_SELECTORS** and **RESPONSE_SELECTORS** empty. If you do so, all
skills are selected at each user utterance and the final response is selected by the skills' confidence.

Also you can include in the Agent configuration any external service running on some other machine.

Services Deployment
===================
1. Create a new **Python 3.7.4** virtual environment.

2. Install requirements for Docker config generator:

    .. code:: bash

        pip install -r gen_requirements.txt

3. Install and configure Docker_ (version 19.03.2 or later) and Docker-compose_ (version 1.19.0 or later).

4. (optional) Install nvidia-docker_ if you wish to run some services on GPU.

   To be able to run GPU-based docker files please make sure about two things on your host system:

    * Your nvidia driver has to support the CUDA version installed in the GPU-based docker file.
    * Please notice that ``docker-compose.yml`` of **3.7** version doesn't officially support `runtime: nvidia`
      option anymore, so you have to manually edit ``/etc/docker/daemon.json`` on your system. Read in the
      nvidia-container-runtime_  documentation how to do it.

5. Create a directory for storing downloaded data, such as pre-trained models.
   It should be located outside the agent project's home directory.

6. Setup an **EXTERNAL_FOLDER** variable with the path to data directory. This pat will be used by Agent to download models' data:

    .. code:: bash

        EXTERNAL_FOLDER=<path to data directory>

7. (optional) If you want to communicate with the Agent via Telegram, setup the following environment variables:

   .. code:: bash

       TELEGRAM_TOKEN=<token>
       TELEGRAM_PROXY=socks5://<user>:<password>@<path:port>

   Here's an example of values:

   .. code:: bash

       TELEGRAM_TOKEN=123456789:AAGCiO0QFb_I-GXL-CbJDw7--JQbHkiQyYA
       TELEGRAM_PROXY=socks5://tgproxy:tgproxy_pwd@123.45.67.89:1447

   If you run the Agent via docker, put this variables into a file and configure it's path under ``AGENT_ENV_FILE``
   variable in the `config file`_. This file name is automatically picked up when the docker-compose file
   is being generated.

8. Configure all skills, skill selectors, response selectors, annotators and database connection in the `config file`_.

   If you want a minimal configuration, you need only one skill.

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

Agent can run both from container and from a local machine. The default Agent port is **4242**.

**Container**
-------------

1. Connect to agent's container:

    .. code:: bash

        docker exec -it agent /bin/bash

    (more information on docker-exec_)

2. Start communicating with the chatbot from the agent's container console:

    .. code:: bash

        python -m core.run

**Local machine**
-----------------

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

        pip install -r gen_requirements.txt

4. Start communicating with the chatbot from the console:

    .. code:: bash

        python -m core.run

    or via the Telegram:

    .. code:: bash

        python -m core.run -ch telegram

**HTTP api server**
-------------------

1. **Run the agent api server from both container and local environment**

    .. code:: bash

        python -m core.run -ch http_client [-p 4242]

    In both cases api will be accessible on your localhost

2. **Web server accepts POST requests with application/json content-type**

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
             http://localhost:4242

    Agent will return a json response:

    .. code:: javascript

        {
          "user_id": "same user id as in request",
          "response": "phrase, which were generated by skills in order to respond"
        }

    In case of wrong format, HTTP errors will be returned.

3.  **Arbitrary input format of the Agent Server**

     If you want to pass anything except
     ``user_id`` and ``payload``, just pass it as an additional key-value item, for example:

     .. code:: bash

        curl --header "Content-Type: application/json" \
             --request POST \
             --data '{"user_id":"xyz","payload":"hello", "my_custom_dialog_id": 111}' \
             http://localhost:4242

     All additional items will be stored into the ``attributes`` field of a ``HumanUtterance``.

4.  **Modify the default response format of the Agent server**

     If you need the Agent server to return something different than ``user_id`` and ``reponse``, try the
     :ref:`output formatters <output-formatters>`.

5. **View dialogs in the database through GET requests**

    The result is returned in json format which can be easily prettifyed with various browser extensions.

    Three main web pages are provided (examples are shown for the case when agent is running on http://localhost:4242):

     * http://localhost:4242/dialogs - provides list of all dialogs (without utterances)
     * http://localhost:4242/dialogs/all - provides list of all dialogs (with utterances)
     * http://localhost:4242/dialogs/<dialog_id> - provides exact dialog (dialog_id can be seen on /dialogs page)


Analyzing the data
==================

All conversations with the Agent are stored to a Mongo DB. When they are dumped, they have
the same format as the Agent's state_. Someone may need to dump and analyze the whole dialogs,
or users, or annotations. For now, the following Mongo collections are available and can be
dumped separately:

    * Human
    * Bot
    * User (Human & Bot)
    * HumanUtterance
    * BotUtterance
    * Utterance (HumanUtterance & BotUtterance)
    * Dialog

To dump a DB collection, make sure that ``mongoengine`` is installed:

    .. code:: bash

        pip install mongoengine==0.17.0

Then run:

    .. code:: bash

         python -m utils.get_db_data [collections]

For example:

    .. code:: bash

         python -m utils.get_db_data Dialog User

Testing HTTP API and automatic processing of predefined dialogs
=================================================================

In order to process predefined dialogs or generate a random one from predefined list of phrases
you can use `utils/http_api_script.py` script.

Make sure that ``aiohttp`` is installed:

    .. code:: bash

        pip install aiohttp==3.5.4

**Processing a predefined dialog**

In this mode the script will pass predefined dialogs from the file ``-df`` to the agent's API.

1. Create a JSON file with a dialog. You can find an example in ``utils/ru_test_dialogs.json``:
    
    .. code:: javascript

          {
              "uuid1": ["phrase1.1", "phrase1.2", "..."],
              "uuid2": ["phrase2.1", "phrase2.2", "..."],
              "uuid3": ["phrase3.1", "phrase3.2", "..."],
          }

2. Run:

    .. code:: bash

         python utils/http_api_test.py -u <api url> -df <dialogs file path>


3. The command line arguments are:
    
    * -u --url - url address of the agent's API
    * -df --datafile - path to a file with predefined dialogs

**Processing a random dialog from predefined phrases**

In this mode the script will generate ``-uc`` dialogs with ``-pc`` phrases in each. Phrases will be selected randomly from the phrase file ``-pf`` and passed to the agent's API.

1. Create a file with sample phrases. This is a simple text file with one phrase per line.

   You can find an example in ``utils/ru_test_phrases.txt``:

2. Run:

    .. code:: bash

         python utils/http_api_test.py -u <api url> -pf <phrases file path> -uc <user count> -pc <phrase per dialog count>

3. The command line arguments are:
    
    * -u --url - url address of the agent's API
    * -pf --phrasefile - path to a file with predefined sample phrases
    * -uc --usercount - number of users taking part in the dialogs
    * -pc --phrasecount - number of phrases in each dialog



Testing Agent in a batch mode
=============================

To test how the Agent replies if it receives a list of utterances, use ``utils/agent_test.py``. Pass a file with
a list of utterances as input. Use the existing ``utils/ru_test_phrases.py`` or create your own file:


    .. code:: bash

         python utils/agent_batch_test.py utils/ru_test_phrases.py



.. _config file: https://github.com/deepmipt/dp-agent/blob/master/config.py
.. _DeepPavlov: https://github.com/deepmipt/DeepPavlov
.. _Docker: https://docs.docker.com/install/
.. _Docker-compose: https://docs.docker.com/compose/install/
.. _nvidia-docker: https://github.com/NVIDIA/nvidia-docker
.. _Docker environment configuration: https://github.com/deepmipt/dp-agent/blob/master/docker-compose.yml
.. _docker-exec: https://docs.docker.com/engine/reference/commandline/exec/
.. _state: https://deeppavlov-agent.readthedocs.io/en/latest/_static/api.html
.. _mongo-docs: https://docs.mongodb.com/manual/tutorial/manage-mongodb-processes/
.. _nvidia-container-runtime: https://github.com/NVIDIA/nvidia-container-runtime