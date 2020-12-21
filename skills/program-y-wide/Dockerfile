FROM python:3.7.4

WORKDIR /src

COPY ./requirements.txt .
RUN pip install -r requirements.txt

COPY . .
WORKDIR /src/dream_aiml/scripts/xnix

CMD ./sanic.sh
