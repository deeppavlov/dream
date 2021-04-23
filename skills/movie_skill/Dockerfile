FROM python:3.8.0

ARG DATABASE_URL

WORKDIR /data
RUN wget ${DATABASE_URL} -q -O /data/database_most_popular_main_info.json

WORKDIR /src
COPY ./skills/movie_skill/requirements.txt .
RUN pip install -r requirements.txt
RUN python -c "import nltk; nltk.download('punkt')"

COPY ./skills/movie_skill ./
COPY ./annotators/CoBotQA/ CoBotQA/
COPY ./common/ common/

CMD gunicorn --workers=1 --bind 0.0.0.0:8023 --timeout=60 server:app --preload
