FROM python:3.7.4

RUN apt-get update && \
    apt-get install -y --no-install-recommends cron && \
    apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false &&  \
	rm -rf /var/lib/apt/lists/* && \
    rm -rf /root/.cache

RUN mkdir /src
RUN mkdir /src/common

COPY ./skills/game_cooperative_skill/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY ./skills/game_cooperative_skill/ /src/
COPY ./common/ /src/common/
WORKDIR /src

# cron
COPY ./skills/game_cooperative_skill/cron/crontab /etc/cron.d/crontab
RUN chmod 0644 /etc/cron.d/crontab
RUN crontab /etc/cron.d/crontab
RUN touch /var/log/cron.log

ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}

# wait for a server answer ( INTERVAL + TIMEOUT ) * RETRIES seconds after that change stutus to unhealthy
HEALTHCHECK --interval=5s --timeout=5s --retries=3 CMD curl --fail 127.0.0.1:${SERVICE_PORT}/healthcheck || exit 1

RUN bash programy_logger_off.sh

CMD bash server_run.sh "gunicorn --workers=2 server:app"
