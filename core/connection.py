from mongoengine import connect

from core.config import HOST, PORT, DB_NAME


state_storage = connect(host=HOST, port=PORT, db=DB_NAME)
