FROM pytorch/pytorch:1.5-cuda10.1-cudnn7-runtime

RUN apt-get update && apt-get install -y --allow-unauthenticated wget && rm -rf /var/lib/apt/lists/*

WORKDIR /src

#create and activate venv
#ENV VIRTUAL_ENV=/parlaivenv
#RUN python3 -m venv $VIRTUAL_ENV
#ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# install parlai
RUN pip install parlai

#create dir for redditgk task
RUN mkdir -p /opt/conda/lib/python3.7/site-packages/parlai/tasks/redditgk
#create dir to use default parlai DATAPATH
RUN mkdir -p /opt/conda/lib/python3.7/site-packages/data
#create dir for data file for redditgk task
RUN mkdir -p /opt/conda/lib/python3.7/site-packages/data/redditgk
#create dir for wow model file
RUN mkdir -p /opt/conda/lib/python3.7/site-packages/data/models/wizard_of_wikipedia
#create dir for courier agent
RUN mkdir -p /opt/conda/lib/python3.7/site-packages/parlai/agents/courier
#

#wget redditgk scripts from cloud
#move task files to tasks/redditgk
RUN wget http://lnsigo.mipt.ru/export/alexaprize_data/parlai_grounding_knowledge/redditgk/__init__.py -q -P /opt/conda/lib/python3.7/site-packages/parlai/tasks/redditgk
RUN wget http://lnsigo.mipt.ru/export/alexaprize_data/parlai_grounding_knowledge/redditgk/agents.py -q -P /opt/conda/lib/python3.7/site-packages/parlai/tasks/redditgk
RUN wget http://lnsigo.mipt.ru/export/alexaprize_data/parlai_grounding_knowledge/redditgk/worlds.py -q -P /opt/conda/lib/python3.7/site-packages/parlai/tasks/redditgk
RUN wget http://lnsigo.mipt.ru/export/alexaprize_data/parlai_grounding_knowledge/redditgk/test.py -q -P /opt/conda/lib/python3.7/site-packages/parlai/tasks/redditgk

#delete old task_list, copy new from cloud
RUN wget http://lnsigo.mipt.ru/export/alexaprize_data/parlai_grounding_knowledge/task_list.py -q -O /opt/conda/lib/python3.7/site-packages/parlai/tasks/task_list.py

#wget courier agent scripts from cloud
#move agent files to agents/courier
RUN wget http://lnsigo.mipt.ru/export/alexaprize_data/parlai_grounding_knowledge/courier/__init__.py -q -P /opt/conda/lib/python3.7/site-packages/parlai/agents/courier
RUN wget http://lnsigo.mipt.ru/export/alexaprize_data/parlai_grounding_knowledge/courier/courier.py -q -P /opt/conda/lib/python3.7/site-packages/parlai/agents/courier

#unzip jsons to the DATAPATH/redditgk
RUN wget http://lnsigo.mipt.ru/export/alexaprize_data/parlai_grounding_knowledge/parlai_redditgk_data.tar.gz -q -P /opt/conda/lib/python3.7/site-packages/data/redditgk
RUN tar -xvzf /opt/conda/lib/python3.7/site-packages/data/redditgk/parlai_redditgk_data.tar.gz -C /opt/conda/lib/python3.7/site-packages/data/redditgk
#RUN rm parlai_redditgk_data.tar.gz

#get wow model tar.gz
RUN wget http://lnsigo.mipt.ru/export/alexaprize_data/parlai_grounding_knowledge/end2end_generator_0.tar.gz -q -P /opt/conda/lib/python3.7/site-packages/data/models/wizard_of_wikipedia

WORKDIR /src

COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt
RUN python -c "import nltk; nltk.download('punkt')"

COPY . /src

CMD gunicorn --workers=1 server:app -b 0.0.0.0:8083
