FROM python:3.7

WORKDIR /app

RUN git clone https://github.com/jkwieser/personality-detection-text.git .

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . src/
