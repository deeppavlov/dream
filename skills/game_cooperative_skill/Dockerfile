FROM python:3.7.4

WORKDIR /src

RUN apt-get update && \
    apt-get install -qy --no-install-recommends cron && \
    apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false &&  \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /root/.cache

COPY ./skills/game_cooperative_skill/requirements.txt .
RUN pip install -r requirements.txt

RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && \
    ./aws/install && \
    rm -rf ./aws awscliv2.zip

COPY ./skills/game_cooperative_skill/ ./
COPY ./common/ ./common/

# cron
COPY ./skills/game_cooperative_skill/cron/crontab /etc/cron.d/crontab
RUN chmod 0644 /etc/cron.d/crontab && \
    crontab /etc/cron.d/crontab && \
    touch /var/log/cron.log


ARG SERVICE_PORT
ENV SERVICE_PORT ${SERVICE_PORT}

# wait for a server answer ( INTERVAL + TIMEOUT ) * RETRIES seconds after that change stutus to unhealthy
HEALTHCHECK --interval=5s --timeout=5s --retries=3 CMD curl --fail 127.0.0.1:${SERVICE_PORT}/healthcheck || exit 1

RUN bash programy_logger_off.sh

CMD bash server_run.sh "gunicorn --workers=2 server:app"
