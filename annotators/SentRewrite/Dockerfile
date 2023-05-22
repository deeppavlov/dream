FROM python:3.7.4

RUN mkdir /src

COPY ./requirements.txt /src/requirements.txt
RUN pip install --upgrade pip && pip install -r /src/requirements.txt

RUN python -c "import neuralcoref;"
RUN python -m spacy download en
RUN python -c "import nltk; nltk.download('punkt')"

COPY . /src/
WORKDIR /src

CMD gunicorn --workers=1 server:app
