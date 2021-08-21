FROM python:3.7.4

WORKDIR /src

COPY ./skills/program-y-dangerous/requirements.txt .
RUN pip install -r requirements.txt

COPY ./skills/program-y-dangerous/ ./
COPY ./common/ ./dream_aiml/src/common/
COPY ./state_formatters/ ./dream_aiml/src/state_formatters/

CMD cd /src/dream_aiml/scripts/xnix && ./sanic.sh
