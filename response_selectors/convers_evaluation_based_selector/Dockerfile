FROM python:3.7.4

RUN mkdir /src
RUN mkdir /src/common

COPY ./response_selectors/convers_evaluation_based_selector/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt
RUN python -c "import nltk; nltk.download('punkt')"

COPY ./response_selectors/convers_evaluation_based_selector/ /src/
COPY ./common/ /src/common/
WORKDIR /src

CMD gunicorn --workers=2 server:app
