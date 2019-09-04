FROM python:3.7.4

RUN mkdir /src
COPY . /src/
WORKDIR /src

RUN pip install -r /src/requirements.txt

CMD cd dream_aiml/scripts/xnix && ./sanic.sh
