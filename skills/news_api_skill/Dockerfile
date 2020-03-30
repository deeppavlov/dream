FROM python:3.7.4

RUN mkdir /src
RUN mkdir /src/common

COPY ./skills/news_api_skill/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt
RUN python -c "import nltk; nltk.download('punkt')"

COPY ./skills/news_api_skill/ /src/
COPY ./common/ /src/common/
WORKDIR /src

CMD gunicorn --workers=1 server:app
