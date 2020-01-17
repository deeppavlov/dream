FROM python:3.7-slim

RUN apt update && apt install git g++ -y

RUN mkdir /src
RUN mkdir /src/src
RUN mkdir /src/data
RUN mkdir /src/news_models_files
RUN mkdir /src/common

RUN mkdir /root/.ssh
COPY ./skills/alexa-prize-news/zdialog-example-deploy-key /root/.ssh/id_rsa
RUN chmod 400 /root/.ssh/id_rsa
RUN touch /root/.ssh/known_hosts
RUN ssh-keyscan gitlab.com >> /root/.ssh/known_hosts

RUN pip install deeppavlov==0.5.0
COPY ./skills/alexa-prize-news/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt
RUN python -m nltk.downloader punkt
RUN python -m nltk.downloader wordnet
RUN python -m nltk.downloader stopwords
RUN python -m nltk.downloader perluniprops
RUN python -m nltk.downloader nonbreaking_prefixes

COPY ./skills/alexa-prize-news/src/ /src/src/
COPY ./common/ /src/common/
ADD http://files.deeppavlov.ai/alexaprize_data/washington_post_data.tar.gz washington_post_data.tar.gz
RUN tar -zxvf washington_post_data.tar.gz -C /src/data
ADD http://files.deeppavlov.ai/alexaprize_data/washington_post_models.tar.gz washington_post_models.tar.gz
RUN tar -zxvf washington_post_models.tar.gz -C /src/news_models_files

COPY ./skills/alexa-prize-news/server.py /src/
COPY ./skills/alexa-prize-news/updater.py /src/

WORKDIR /src

CMD bash -c "python updater.py | gunicorn --workers=1 server:app -b 0.0.0.0:8027 -t 600"

