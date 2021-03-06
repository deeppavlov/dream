FROM deeppavlov/base-gpu:0.12.1

ARG CONFIG
ARG DATA_URL=http://files.deeppavlov.ai/alexaprize_data/ood_dbdc_torch_bert_v2.tar.gz
ARG PORT
ENV CONFIG=$CONFIG
ENV PORT=$PORT

RUN mkdir /models


RUN wget ${DATA_URL} -O /models/ood_dbdc_torch_bert_v2.tar.gz && \
    tar zxfv /models/ood_dbdc_torch_bert_v2.tar.gz -C /models/ && \
    rm -f /models/ood_dbdc_torch_bert_v2.tar.gz

WORKDIR /src
RUN mkdir common

COPY annotators/dialog_breakdown/requirements.txt .
RUN pip install -r requirements.txt

COPY annotators/dialog_breakdown/ ./
COPY common/ common/

RUN python -m deeppavlov install $CONFIG
CMD gunicorn --workers=1 --bind 0.0.0.0:8082 --timeout=300 server:app
