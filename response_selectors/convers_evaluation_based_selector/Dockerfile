FROM python:3.7.4

WORKDIR /src

COPY ./response_selectors/convers_evaluation_based_selector/requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN python -c "import nltk; nltk.download('punkt')"

COPY ./response_selectors/convers_evaluation_based_selector/ ./
COPY ./common/ ./common/

CMD gunicorn --workers=2 server:app
