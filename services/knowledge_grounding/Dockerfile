FROM pytorch/pytorch:1.5-cuda10.1-cudnn7-runtime

RUN apt-get update && apt-get install -y --allow-unauthenticated git wget && rm -rf /var/lib/apt/lists/*

WORKDIR /src

# install parlai
RUN pip install git+https://github.com/Saraharas/ParlAI@v0.9.4-kg#egg=ParlAI

# create dirs for data and models
RUN mkdir -p /opt/conda/lib/python3.7/site-packages/data/models

#load data
RUN wget http://lnsigo.mipt.ru/export/alexaprize_data/parlai_grounding_knowledge/parlai_topical_chat_data.tar.gz -q -P /opt/conda/lib/python3.7/site-packages/data &&\
tar -xvzf /opt/conda/lib/python3.7/site-packages/data/parlai_topical_chat_data.tar.gz -C /opt/conda/lib/python3.7/site-packages/data &&\
rm /opt/conda/lib/python3.7/site-packages/data/parlai_topical_chat_data.tar.gz

# load model tar.gz
RUN wget http://lnsigo.mipt.ru/export/alexaprize_data/parlai_grounding_knowledge/topical_chat_blender90_1_sent_48_epochs.tar.gz -q -P /opt/conda/lib/python3.7/site-packages/data/models &&\
tar -xvzf /opt/conda/lib/python3.7/site-packages/data/models/topical_chat_blender90_1_sent_48_epochs.tar.gz -C /opt/conda/lib/python3.7/site-packages/data/models &&\
rm /opt/conda/lib/python3.7/site-packages/data/models/topical_chat_blender90_1_sent_48_epochs.tar.gz

WORKDIR /src

COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt
RUN python -c "import nltk; nltk.download('punkt')"

COPY . /src

CMD gunicorn --workers=1 server:app -b 0.0.0.0:8083
