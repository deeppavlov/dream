FROM python:3.7.4
RUN mkdir /src
RUN mkdir /global_data
RUN wget http://lnsigo.mipt.ru/export/alexaprize_data/tfidf_dialogs/dialog_list_v33.json -O /global_data/dialog_list.json
RUN wget http://lnsigo.mipt.ru/export/alexaprize_data/tfidf_dialogs/bad_dialog_list_v33.json -O /global_data/bad_dialog_list.json
RUN wget http://lnsigo.mipt.ru/export/models/new_vectorizer_2.zip -O /global_data/new_vectorizer_2.zip
COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY . /src
WORKDIR /src



CMD gunicorn --workers=2 server:app
