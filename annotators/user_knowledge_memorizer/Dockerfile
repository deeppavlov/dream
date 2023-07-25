FROM python:3.9.1

WORKDIR /src

ARG SERVICE_PORT
ARG SRC_DIR

ENV SERVICE_PORT=$SERVICE_PORT

RUN pip install -U pip wheel setuptools

COPY ./annotators/user_knowledge_memorizer/requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache -r /src/requirements.txt && \
    python -m nltk.downloader wordnet && \
    pip install git+https://github.com/deeppavlov/custom_kg_svc.git@feat/support_index
    
COPY $SRC_DIR .


CMD gunicorn --workers=1 server:app -b 0.0.0.0:$SERVICE_PORT