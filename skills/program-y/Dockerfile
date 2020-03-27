FROM python:3.7.4

RUN mkdir /src
RUN mkdir /src/common

COPY ./skills/program-y/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY ./skills/program-y/ /src/
COPY ./common/ /src/common/
WORKDIR /src

CMD cd dream_aiml/scripts/xnix && ./sanic.sh
