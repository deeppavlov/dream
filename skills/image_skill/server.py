from io import BytesIO
from os import getenv
from uuid import uuid4
from urllib.parse import urlparse

import requests
from PIL import Image
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

FILE_SERVER_URL = getenv('FILE_SERVER_URL')
file_server = urlparse(FILE_SERVER_URL)


class Payload(BaseModel):
    url: str


@app.post('/')
def make_black_and_white(payload: Payload):
    resp = requests.get(payload.url)
    resp.raise_for_status()
    image = Image.open(BytesIO(resp.content))
    image = image.convert('1')  # monochrome
    ans = BytesIO()
    image.save(ans, 'JPEG')
    ans.seek(0)
    fname = f'{uuid4().hex}.jpg'
    resp = requests.post(FILE_SERVER_URL, files={'file': (fname, ans, 'image/jpg')})
    ans_link = resp.json()['downloadLink']
    ans_link = urlparse(ans_link)._replace(scheme=file_server.scheme, netloc=file_server.netloc).geturl()
    return [[{'text': '', 'image': ans_link}]]


# 'http://localhost:3000/file?file=e9bcb969fcc6406980dfed7198facb2e.jpg'