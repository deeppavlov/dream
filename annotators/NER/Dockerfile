FROM pytorch/pytorch:1.2-cuda10.0-cudnn7-runtime

RUN mkdir /src

COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

RUN pip uninstall -y bson pymongo && pip install bson==0.5.7 && pip install pymongo==3.7.2
COPY ./download_flair_model.py /src/download_flair_model.py
RUN python /src/download_flair_model.py

ENV DEVICE cpu

COPY . /src/
WORKDIR /src


CMD gunicorn --workers=1 server:app --preload
