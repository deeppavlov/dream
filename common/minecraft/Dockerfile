FROM nikolaik/python-nodejs:latest


COPY common/minecraft/requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY common/minecraft/package.json package.json
RUN npm install

COPY ./common/minecraft /src
WORKDIR /src

CMD python bot.py
