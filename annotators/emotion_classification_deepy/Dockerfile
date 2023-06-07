FROM deeppavlov/base-gpu:0.12.0

COPY ./requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

WORKDIR /app
COPY . .

RUN python -m deeppavlov download emo_bert.json