FROM python:3.8

WORKDIR /src
# COPY ./annotators/vidchapters_service /src/

RUN pwd
RUN ls /src

RUN pip install --upgrade pip
RUN pip install gdown
COPY ./annotators/vidchapters_service/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

RUN git clone https://github.com/antoyang/VidChapters.git /src/aux_files/VidChapters
# RUN pip install -r /src/aux_files/VidChapters/requirements.txt
RUN ls /src/aux_files/VidChapters

RUN touch /src/__init__.py && \
    touch /src/aux_files/__init__.py && \
    touch /src/aux_files/VidChapters/__init__.py

RUN ls /src

# RUN wget -V
RUN wget -O /src/aux_files/checkpoint_vidchapters https://drive.google.com/file/d/1jbmfuB44p3twrlqnfIv6cCM3Oyqk-zeh
RUN gdown --fuzzy https://drive.google.com/file/d/1qmQcEkDDlnkAkRd6BIrVoArBv6Sg1Lv7/view -O /src/aux_files/captioning_model.pth -c --no-check-certificate
# RUN mv -f models_v0 /data/models && ls /data/models && rm -rf models_v0

RUN pip install git+https://github.com/openai/whisper.git 
RUN pip install git+https://github.com/m-bain/whisperx.git 

ENV PYTHONPATH "${PYTHONPATH}:/src/aux_files/VidChapters"

