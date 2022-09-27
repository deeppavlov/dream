# syntax=docker/dockerfile:experimental
FROM pytorch/pytorch:1.5-cuda10.1-cudnn7-runtime

RUN apt-get update && apt-get install -y gnupg2
RUN apt install -y curl
RUN apt-get install -y --allow-unauthenticated wget

#RUN apt-get install -y gcc-5 g++-5
#RUN update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-5 60 --slave /usr/bin/g++ g++ /usr/bin/g++-5
#
#RUN apt-get install aptitude
#RUN aptitude install build-essential
# https://github.com/rusty1s/pytorch_scatter/issues/47

RUN apt-key del 7fa2af80  && \
    rm -f /etc/apt/sources.list.d/cuda*.list && \
    curl https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/cuda-keyring_1.0-1_all.deb \
    -o cuda-keyring_1.0-1_all.deb && \
    dpkg -i cuda-keyring_1.0-1_all.deb

WORKDIR /src

ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}
ARG MODELS_URL
ENV MODELS_URL ${MODELS_URL}
ARG BART_MODEL_NAME
ENV BART_MODEL_NAME ${BART_MODEL_NAME}
ARG FINETUNED_MODEL_NAME
ENV FINETUNED_MODEL_NAME ${FINETUNED_MODEL_NAME}

WORKDIR /data
RUN wget ${MODELS_URL} -O ./finetuned2.tar.gz && \
    tar zxfv ./finetuned2.tar.gz
WORKDIR /src

COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt
RUN python -c "import nltk; nltk.download('punkt')"
RUN python -c "import nltk; nltk.download('stopwords')"
RUN python -c "from transformers import BartForConditionalGeneration; BartForConditionalGeneration.from_pretrained('${BART_MODEL_NAME}', forced_bos_token_id=0)"
RUN python -c "from transformers import BartTokenizer; BartTokenizer.from_pretrained('${BART_MODEL_NAME}')"
RUN python -c "from transformers import GPT2Tokenizer; GPT2Tokenizer.from_pretrained('${FINETUNED_MODEL_NAME}')"
RUN python -c "from transformers import GPT2LMHeadModel; model = GPT2LMHeadModel.from_pretrained('${FINETUNED_MODEL_NAME}')"

COPY . /src

CMD gunicorn --workers=1 server:app -b 0.0.0.0:${SERVICE_PORT} --timeout=3
