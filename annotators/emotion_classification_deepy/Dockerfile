FROM deeppavlov/base-gpu:0.12.0
RUN pip install --upgrade pip && pip install git+https://github.com/deeppavlov/DeepPavlov.git@0.12.0

COPY ./requirements.txt .
RUN pip install -r requirements.txt

WORKDIR /app
COPY . .

RUN python -m deeppavlov download emo_bert.json