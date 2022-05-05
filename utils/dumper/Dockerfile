FROM python:3.9.12-buster

WORKDIR /app

VOLUME /data

RUN apt update && \
    apt install -y --no-install-recommends \
        cron && \
        touch /var/log/cron.log && \
        rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install -r requirements.txt && \
    rm -rf /root/.cache

COPY run-app /etc/cron.d/

RUN crontab /etc/cron.d/run-app

COPY main.py .

CMD printenv | grep 'AGENT_URL' > /etc/environment && cron && tail -f /var/log/cron.log
