FROM python:3.7.4

RUN mkdir /src

COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt && \
    python -m deeppavlov install brillmoore_wikitypos_en && \
    python -m deeppavlov download brillmoore_wikitypos_en

WORKDIR /app
COPY . .

CMD gunicorn --workers=2 server:app
