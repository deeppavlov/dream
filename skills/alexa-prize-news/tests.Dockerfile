FROM python:3.7-slim

RUN apt update && apt install git g++ -y

RUN mkdir /root/.ssh
COPY zdialog-example-deploy-key /root/.ssh/id_rsa
RUN chmod 400 /root/.ssh/id_rsa
RUN touch /root/.ssh/known_hosts
RUN ssh-keyscan gitlab.com >> /root/.ssh/known_hosts

RUN pip install deeppavlov==0.5.0
RUN pip install pytest
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt
RUN python -m nltk.downloader punkt
RUN python -m nltk.downloader wordnet
RUN python -m nltk.downloader stopwords
RUN python -m nltk.downloader perluniprops
RUN python -m nltk.downloader nonbreaking_prefixes

RUN mkdir /src
COPY src /src
WORKDIR /src

CMD ["pytest", "tests"]
