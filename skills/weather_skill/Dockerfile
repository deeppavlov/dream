FROM python:3.8.0

WORKDIR /src

RUN mkdir /data && \
    wget https://files.deeppavlov.ai/dream/weather_skill/openweathermap_city.list.json -O /data/openweathermap_city.list.json

COPY ./skills/weather_skill/requirements.txt .
RUN pip install -r requirements.txt

#COPY ./weather_service/ /src/skills/weather_skill
#COPY ./CoBotQA/ /src/skills/CoBotQA
ENV WEATHER_QUESTIONS_PATH='/src/data/weather_questions.json'
COPY ./skills/weather_skill/ ./
COPY ./common/ ./common/

CMD gunicorn --workers=1 server:app
