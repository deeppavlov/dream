FROM python:3.7.4

WORKDIR /src

COPY ./skills/program-y/requirements.txt .
RUN pip install -r requirements.txt

COPY ./skills/program-y/ ./
COPY ./common/ ./common/

CMD cd dream_aiml/scripts/xnix && ./sanic.sh
