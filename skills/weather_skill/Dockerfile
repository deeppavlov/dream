FROM python:3.8.0

RUN mkdir /src

COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

#COPY ./weather_service/ /src/skills/weather_skill
#COPY ./CoBotQA/ /src/skills/CoBotQA
COPY . /src/
WORKDIR /src

CMD gunicorn --workers=1 server:app
