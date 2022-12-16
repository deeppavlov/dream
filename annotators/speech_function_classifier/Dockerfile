FROM pytorch/pytorch:1.9.0-cuda10.2-cudnn7-runtime

WORKDIR /src

RUN apt-get update && apt-get install -y --allow-unauthenticated git curl && rm -rf /var/lib/apt/lists/*

RUN mkdir /models && \
    curl https://files.deeppavlov.ai/alexaprize_data/speech_function_classifier.tar.gz --output arch.tgz && \
    tar zxfv arch.tgz && \
    rm -rf arch.tgz && \
    curl https://files.deeppavlov.ai/dream/speech_function_classifier/res_cor.json --output data/res_cor.json && \
    mv data/* /models && \
    rm -rf data

COPY annotators/speech_function_classifier/requirements.txt requirements.txt

RUN pip install -r requirements.txt

RUN python -c "import nltk; nltk.download('punkt')"

COPY . ./

ARG SERVICE_NAME
ENV SERVICE_NAME ${SERVICE_NAME}

ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT}