FROM deeppavlov/base-gpu:0.12.1
RUN pip install git+https://github.com/deeppavlov/DeepPavlov.git@0.12.1

#RUN rm DeepPavlov

#Set up git lfs for your user account: git lfs install
WORKDIR /base
RUN rm -rf DeepPavlov
RUN git clone https://github.com/dimakarp1996/DeepPavlov.git 
WORKDIR /base/DeepPavlov
RUN git checkout pal-bert+ner

ARG CONFIG

ARG PORT
ENV CONFIG=$CONFIG
ENV PORT=$PORT

WORKDIR /src
RUN mkdir common

COPY annotators/combined_classification/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

COPY annotators/combined_classification/ ./
COPY common/ common/

CMD gunicorn --workers=1 --bind 0.0.0.0:8087 --timeout=300 server:app
