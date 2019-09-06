from mongoengine import connect

from core.transform_config import DB_HOST, DB_PORT, DB_NAME

state_storage = connect(host=DB_HOST, port=DB_PORT, db=DB_NAME)
