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

RUN sed -in '/args.model_name = os.path.join(os.environ\[\"TRANSFORMERS_CACHE\"\], args.model_name)/d' /src/aux_files/VidChapters/demo_vid2seq.py
RUN sed -i "s/t5-base/google-t5\/t5-base/" /src/aux_files/VidChapters/args.py
RUN cat /src/aux_files/VidChapters/args.py
RUN sed -i "s/local_files_only=True/local_files_only=False/" /src/aux_files/VidChapters/model/vid2seq.py
# RUN cat /src/aux_files/VidChapters/model/vid2seq.py

RUN wget -O /src/aux_files/checkpoint_vidchapters https://drive.google.com/file/d/1jbmfuB44p3twrlqnfIv6cCM3Oyqk-zeh
RUN gdown --fuzzy https://drive.google.com/file/d/1qmQcEkDDlnkAkRd6BIrVoArBv6Sg1Lv7/view -O /src/aux_files/captioning_model.pth -c --no-check-certificate

# RUN pip install git+https://github.com/openai/whisper.git 
# RUN pip install git+https://github.com/m-bain/whisperx.git 

COPY ./annotators/vidchapters_service /src/

RUN apt-get update && apt-get install -y ffmpeg
# ENV PYTHONPATH="${PYTHONPATH}:/src"

RUN python -c "import whisper; whisper.load_model('large-v2', device='cpu', download_root='/src/aux_files/TOFILL')"

# ENV HF_HOME="~/.cache/huggingface/hub"
# RUN export TRANSFORMERS_CACHE=~/.cache/huggingface/hub