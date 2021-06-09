FROM tensorflow/tensorflow:1.14.0-py3

ARG DATA_URL
ENV DATA_URL ${DATA_URL}

ADD $DATA_URL /root/model/

WORKDIR /app

RUN tar -xvzf /root/model/*.tar.gz -C /root/model

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

ENV MODEL_PATH /root/model/convert_single_context
ENV TOPIC_DIALOGS_PATH /root/model/dialogs_topic.json
ENV NP_DIALOGS_PATH /root/model/dialogs_np.json

COPY . .

CMD gunicorn --workers=2 server:app --timeout 120
