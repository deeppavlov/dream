FROM python:3.10

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .

CMD cd dream_aiml/scripts/xnix && ./sanic.sh
