from mongoengine import connect

from os import getenv
from core.config import HOST, PORT, DB_NAME

if getenv('LAUNCHING_ENVIRONMENT') != 'docker':
    HOST = '0.0.0.0'

state_storage = connect(host=HOST, port=PORT, db=DB_NAME)
