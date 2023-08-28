FROM python:3.7

WORKDIR /src

RUN git clone https://github.com/jkwieser/personality-detection-text.git /personality-detection-text

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .
