FROM tensorflow/tensorflow:1.14.0-py3

RUN mkdir /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl &&\
    apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false && \
	rm -rf /var/lib/apt/lists/* && \
    rm -rf /root/.cache

RUN mkdir -p /root/model && \
    curl http://files.deeppavlov.ai/alexaprize_data/dummy_skill_dialog.tar.gz > /root/model/dummy_skill_dialog.tar.gz && \
    cd /root/model/ && \
    tar -xvzf dummy_skill_dialog.tar.gz

COPY ./requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

ENV MODEL_PATH /root/model/convert_single_context
ENV TOPIC_DIALOGS_PATH /root/model/dialogs_topic.json
ENV NP_DIALOGS_PATH /root/model/dialogs_np.json

COPY . /app/
WORKDIR /app

CMD gunicorn --workers=2 server:app --timeout 120
