FROM python:3.8.4

RUN mkdir /src

COPY ./annotators/rake_keywords/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt
RUN python -c "import nltk; nltk.download('stopwords')"

COPY ./annotators/rake_keywords/ /src/
COPY ./common/ /src/common/

WORKDIR /src

CMD gunicorn --workers=2 server:app
