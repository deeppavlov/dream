FROM python:3.7.4

RUN mkdir /src
RUN mkdir /src/common

COPY ./skills/game_cooperative_skill/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY ./skills/game_cooperative_skill/ /src/
COPY ./common/ /src/common/
WORKDIR /src

RUN bash programy_logger_off.sh

CMD gunicorn --workers=2 server:app
