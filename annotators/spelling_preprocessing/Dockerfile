FROM python:3.7.4

RUN mkdir /src

COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

RUN python -m deeppavlov install brillmoore_wikitypos_en
RUN python -m deeppavlov download brillmoore_wikitypos_en

COPY . /src/
WORKDIR /src

CMD gunicorn --workers=2 server:app
