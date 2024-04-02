FROM python:3.7

WORKDIR /src

COPY . /src
RUN mkdir /data

COPY requirements.txt .

RUN pip install -r requirements.txt

RUN wget -O models http://files.deeppavlov.ai/dream_data/personality_detection/personality_detection_models_v0.tar.gz && tar -xf models
RUN mv -f models_v0 /data/models && ls /data/models && rm -rf models_v0

COPY . .
