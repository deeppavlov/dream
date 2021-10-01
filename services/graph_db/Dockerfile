from python:3.8

WORKDIR /app

RUN pip install neo4j==4.2.1

COPY client.py client.py
COPY fill_db.py fill_db.py
COPY server.py server.py
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

CMD tail -f /dev/null
