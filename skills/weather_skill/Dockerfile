FROM python:3.8.0

RUN mkdir /src
RUN mkdir /src/common

COPY ./skills/weather_skill/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

#COPY ./weather_service/ /src/skills/weather_skill
#COPY ./CoBotQA/ /src/skills/CoBotQA
ENV WEATHER_QUESTIONS_PATH='/src/data/weather_questions.json'
COPY ./skills/weather_skill/ /src/
COPY ./common/ /src/common/
WORKDIR /src

CMD gunicorn --workers=1 server:app
