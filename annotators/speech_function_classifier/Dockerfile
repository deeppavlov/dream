FROM deeppavlov/base-gpu:0.14.1

WORKDIR /src

COPY ./annotators/speech_function_classifier/requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY ./annotators/speech_function_classifier/* ./
COPY ./common ./common

RUN python models.py

ARG SERVICE_NAME
ENV SERVICE_NAME ${SERVICE_NAME}

ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}
