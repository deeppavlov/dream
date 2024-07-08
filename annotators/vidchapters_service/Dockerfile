FROM python:3.8

WORKDIR /src

RUN pip install --upgrade pip
RUN pip install gdown
COPY ./annotators/vidchapters_service/requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt
# RUN ls /src
# RUN which clip

RUN git clone https://github.com/antoyang/VidChapters.git /src/aux_files/VidChapters

RUN touch /src/__init__.py && \
    touch /src/aux_files/__init__.py && \
    touch /src/aux_files/VidChapters/__init__.py


RUN wget -O /src/aux_files/checkpoint_vidchapters https://drive.google.com/file/d/1jbmfuB44p3twrlqnfIv6cCM3Oyqk-zeh
RUN gdown --fuzzy https://drive.google.com/file/d/1qmQcEkDDlnkAkRd6BIrVoArBv6Sg1Lv7/view -O /src/aux_files/captioning_model.pth -c --no-check-certificate

RUN pip install git+https://github.com/openai/whisper.git 
RUN pip install git+https://github.com/m-bain/whisperx.git 

COPY ./annotators/vidchapters_service /src/

RUN pip list
RUN pwd

# RUN sudo apt update && sudo apt install ffmpeg
# RUN sudo apt install ffmpeg

# ENV PYTHONPATH "${PYTHONPATH}:/src/aux_files/VidChapters"
