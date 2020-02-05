FROM pytorch/pytorch:1.2-cuda10.0-cudnn7-runtime

RUN apt-get update && apt-get install -y --allow-unauthenticated git curl && rm -rf /var/lib/apt/lists/*

WORKDIR /comet

RUN git clone https://github.com/atcbosselut/comet-commonsense.git .
RUN git reset --hard de71afa4407816033320b91ae458216329a35fa8

WORKDIR /comet/pretrained_models
RUN curl http://lnsigo.mipt.ru/export/alexaprize_data/comet/atomic_pretrained_model.pickle > atomic_pretrained_model.pickle

WORKDIR /comet/data/atomic/processed/generation/
RUN curl http://lnsigo.mipt.ru/export/alexaprize_data/comet/categories_oEffect\%23oReact\%23oWant\%23xAttr\%23xEffect\%23xIntent\%23xNeed\%23xReact\%23xWant-maxe1_17-maxe2_35-maxr_1.pickle > categories_oEffect\#oReact\#oWant\#xAttr\#xEffect\#xIntent\#xNeed\#xReact\#xWant-maxe1_17-maxe2_35-maxr_1.pickle

WORKDIR /comet
RUN curl http://lnsigo.mipt.ru/export/alexaprize_data/comet/model.tar.gz > model.tar.gz
RUN tar -xvzf model.tar.gz
RUN rm model.tar.gz

WORKDIR /comet

COPY ./requirements.txt /comet/requirements.txt
RUN pip install -r /comet/requirements.txt
RUN python -m spacy download en

COPY . /comet/
WORKDIR /comet

CMD gunicorn --workers=1 server:app -b 0.0.0.0:8053
