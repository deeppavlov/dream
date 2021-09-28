FROM deeppavlov/base-gpu:0.14.1

WORKDIR /src

COPY ./annotators/speech_function_classifier/requirements.txt requirements.txt

RUN pip install -r requirements.txt

RUN python -c "import nltk; nltk.download('punkt')"

COPY ./annotators/speech_function_classifier ./
COPY ./common ./common

RUN python models.py

ARG SERVICE_NAME
ENV SERVICE_NAME ${SERVICE_NAME}

ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT}