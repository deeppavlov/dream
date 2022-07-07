FROM python:3.7.4

RUN mkdir /src
RUN mkdir /src/common

ARG LANGUAGE=EN
ENV LANGUAGE ${LANGUAGE}

COPY ./skills/personal_info_skill/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY ./skills/personal_info_skill/ /src/
COPY ./common/ /src/common/
WORKDIR /src

CMD gunicorn --workers=2 server:app
