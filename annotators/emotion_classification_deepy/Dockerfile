FROM deeppavlov/base-gpu:0.12.0
RUN pip install git+https://github.com/deeppavlov/DeepPavlov.git@0.12.0

WORKDIR /app
COPY . .

RUN python -m deeppavlov download emo_bert.json