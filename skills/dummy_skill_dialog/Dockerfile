FROM tensorflow/tensorflow:1.14.0-py3

RUN apt-get update && apt-get install -y --allow-unauthenticated wget && rm -rf /var/lib/apt/lists/*

ARG DATA_URL
ENV DATA_URL ${DATA_URL}
ENV MODEL_PATH /root/model/convert_single_context
ENV TOPIC_DIALOGS_PATH /root/model/dialogs_topic.json
ENV NP_DIALOGS_PATH /root/model/dialogs_np.json

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

RUN mkdir /root/model/

RUN wget $DATA_URL -q -P /root/model/
RUN tar -xvzf /root/model/*.tar.gz -C /root/model

COPY . .

CMD gunicorn --workers=2 server:app --timeout 120
